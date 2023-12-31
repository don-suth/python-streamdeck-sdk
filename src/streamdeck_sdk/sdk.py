import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Callable, Coroutine
from collections import defaultdict

import pydantic
import websockets

from . import event_routings
from . import mixins
from .logger import init_root_logger, log_errors_async, rename_plugin_logger
from .sd_objs import registration_objs, events_received_objs

logger = logging.getLogger(__name__)


class Base(
		mixins.PluginEventHandlersMixin,
		mixins.ActionEventHandlersMixin,
		mixins.PluginEventsSendMixin,
		mixins.ActionEventsSendMixin,
		mixins.SendMixin,
		):
	pass


class Action(Base):
	"""
	Base Action class.

	Attributes:
		UUID: The unique identifier of the action. e.g. "com.example.plugin.action"
	"""
	UUID: str

	def __init__(self):
		self.plugin_uuid: Optional[str] = None
		self.ws: Optional[websockets.WebSocketClientProtocol] = None
		self.info: Optional[registration_objs.Info] = None
		self.instance_settings: defaultdict[str, dict] = defaultdict(dict)
		self.sd: Optional[StreamDeck] = None


class ExtrasAction(mixins.ExtraKeyEventHandlersMixin, Action):
	"""	Adds the on_key_long_press and on_key_double_press events to the action.
	"""
	pass


class StreamDeck(Base):
	"""
	Main class for handling the plugin.
	Initialise with a list of actions.
	"""
	def __init__(
			self,
			actions: List[Action],
			*,
			log_file: Optional[Path] = None,
			log_level: int = logging.DEBUG,
			log_max_bytes: int = 3 * 1024 * 1024,  # eg 3 MB maximum
			log_backup_count: int = 2,
			):

		if log_file is not None:
			self.log_file: Path = Path(log_file)
			init_root_logger(
				log_file=self.log_file,
				log_level=log_level,
				log_max_bytes=log_max_bytes,
				log_backup_count=log_backup_count,
				)

		self.actions_list: List[Action] = actions
		self.registered_actions: Dict[str, Action] = {}

		self.ws: Optional[websockets.WebSocketClientProtocol] = None
		self.port: Optional[int] = None
		self.plugin_uuid: Optional[str] = None
		self.register_event: Optional[str] = None
		self.info: Optional[registration_objs.Info] = None
		self.registration_dict: Optional[dict] = None
		self.active_tasks: set[asyncio.Task] = set()
		self.global_settings: dict = dict()
		self.instance_settings: defaultdict[str, dict] = defaultdict(dict)

	@log_errors_async
	async def run(self) -> None:
		"""
		Main entrypoint for your plugin.
		"""
		logger.debug("Plugin has been started")

		parser = argparse.ArgumentParser(
			description="Streamdeck Plugin",
			)
		parser.add_argument('-port', dest='port', type=int, help="Port", required=True)
		parser.add_argument('-pluginUUID', dest='pluginUUID', type=str, help="PluginUUID", required=True)
		parser.add_argument('-registerEvent', dest='registerEvent', type=str, help="RegisterEvent", required=True)
		parser.add_argument('-info', dest='info', type=str, help="Info", required=True)
		args = parser.parse_args()

		self.info: registration_objs.Info = registration_objs.Info.model_validate(json.loads(args.info))
		rename_plugin_logger(self.info.plugin.uuid)
		logger.debug(f"{self.info=}")

		self.port: int = args.port
		logger.debug(f"{self.port=}")
		self.plugin_uuid: str = args.pluginUUID
		logger.debug(f"{self.plugin_uuid=}")
		self.register_event: str = args.registerEvent
		logger.debug(f"{self.register_event=}")

		self.registration_dict = {"event": self.register_event, "uuid": self.plugin_uuid}
		logger.debug(f"{self.registration_dict=}")

		await self.__start_ws_connection()

	def __init_actions(self) -> None:
		"""
		Helper function to initialise the actions.
		Run once, when the plugin starts.
		"""
		if self.actions_list is None:
			return

		for action in self.actions_list:
			try:
				action_uuid = action.UUID
			except AttributeError as exception:
				action_class = str(action.__class__)
				error_message = f"{action_class} must have attribute UUID"
				logger.error(error_message, exc_info=True)
				raise AttributeError(error_message) from exception
			action.ws = self.ws
			action.plugin_uuid = self.plugin_uuid
			action.info = self.info
			action.sd = self
			self.registered_actions[action_uuid] = action

	@log_errors_async
	async def __handle_ws_message(
			self,
			message: str,
			) -> None:
		"""
		Handles communication from the Streamdeck software,
		constructs the relevant objects, and routes them to
		the appropriate Plugin/Action event handlers.
		"""
		message_dict = json.loads(message)
		logger.debug(f"{message_dict=}")

		# Route the message to the appropriate handle.
		event = message_dict["event"]
		logger.debug(f"{event=}")

		event_routing = event_routings.EVENT_ROUTING_MAP.get(event)
		if event_routing is None:
			logger.warning("event_routing is None")
			return

		obj = event_routing.obj_type.model_validate(message_dict)
		logger.debug(f"{obj=}")

		# Schedule the handlers to run, instead of waiting for them.
		self.schedule_task_soon(self.route_event_in_plugin_handler(event_routing=event_routing, obj=obj))
		if event_routing.type == event_routings.EventRoutingObjTypes.ACTION:
			self.schedule_task_soon(self.route_action_event_in_action_handler(event_routing=event_routing, obj=obj))
		elif event_routing.type == event_routings.EventRoutingObjTypes.PLUGIN:
			self.schedule_task_soon(self.route_plugin_event_in_action_handlers(event_routing=event_routing, obj=obj))

	@log_errors_async
	async def route_event_in_plugin_handler(
			self,
			event_routing: event_routings.EventRoutingObj,
			obj: pydantic.BaseModel
			) -> None:
		"""
		If the plugin itself is listening for any events,
		this routes them there.
		"""
		try:
			handler: Callable[[pydantic.BaseModel], Coroutine[None]] = getattr(self, event_routing.handler_name)
		except AttributeError as err:
			logger.error(f"Handler missing: {str(err)}", exc_info=True)
			return
		self.schedule_task_soon(handler(obj))

	@log_errors_async
	async def route_action_event_in_action_handler(
			self,
			event_routing: event_routings.EventRoutingObj,
			obj: pydantic.BaseModel,
			) -> None:
		"""
		If the Streamdeck message is for a particular Action,
		then this routes it to the appropriate event handler.
		"""
		try:
			action_uuid = getattr(obj, "action")
		except AttributeError as err:
			logger.error(f"Action UUID is missing: {str(err)}", exc_info=True)
			return

		action_obj = self.registered_actions.get(action_uuid)
		if action_obj is None:
			logger.warning(f"{action_uuid=} not registered.")
			return

		try:
			handler: Callable[[pydantic.BaseModel], Coroutine[None]] = getattr(action_obj, event_routing.handler_name)
		except AttributeError as err:
			logger.error(f"Handler missing: {str(err)}", exc_info=True)
			return

		self.schedule_task_soon(handler(obj))

	@log_errors_async
	async def route_plugin_event_in_action_handlers(
			self,
			event_routing: event_routings.EventRoutingObj,
			obj: pydantic.BaseModel,
			) -> None:
		"""
		If any Actions are listening for any Plugin events, this
		will route them to the appropriate event handler.
		"""
		for action_obj in self.registered_actions.values():
			try:
				handler: Callable[[pydantic.BaseModel], Coroutine[None]] = getattr(action_obj, event_routing.handler_name)
			except AttributeError as err:
				logger.error(f"Handler missing: {str(err)}", exc_info=True)
				return
			self.schedule_task_soon(handler(obj))

	@log_errors_async
	async def __start_ws_connection(self) -> None:
		"""
		Opens the Websocket connection to the Streamdeck software,
		and starts listening for events.
		"""
		ws_uri = f"ws://localhost:{self.port}"
		async for websocket in websockets.connect(ws_uri):
			self.ws = websocket
			logger.debug("Websocket opened")
			self.__init_actions()
			await self.send(self.registration_dict)
			try:
				async for message in websocket:
					await self.__handle_ws_message(message)
			except websockets.ConnectionClosed as closed_connection:
				logger.info("Connection closed. Shutting down.")
				logger.debug(f"{closed_connection.recv.code=} {closed_connection.recv.reason=}")
				return

	def schedule_task_soon(self, coro: Coroutine) -> asyncio.Task:
		"""Schedules a task to be done on the next cycle of the event loop.
		The Task is kept in self.active_tasks, and a callback is added to
		remove it from that set when the task is complete.

		Args:
			coro: The Coroutine to schedule.

		Returns: The resulting task object.

		"""
		task = asyncio.create_task(coro=coro)
		self.active_tasks.add(task)
		task.add_done_callback(self.active_tasks.discard)
		return task

	async def _on_did_receive_global_settings(self, obj: events_received_objs.DidReceiveGlobalSettings) -> None:
		"""Update the local copy of the global settings."""
		self.global_settings.update(obj.payload.settings)
		await self.on_did_receive_global_settings(obj=obj)

	async def _on_did_receive_settings(self, obj: events_received_objs.DidReceiveSettings) -> None:
		"""Update the local copy of the context settings, and the settings of that action object."""
		action = obj.action
		context = obj.context
		self.instance_settings[context].update(obj.payload.settings)
		self.registered_actions[action].instance_settings[context].update(obj.payload.settings)
		await self.on_did_receive_settings(obj=obj)
