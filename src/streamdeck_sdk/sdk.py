import json
from pathlib import Path
import logging

import websockets
import asyncio
import argparse

from typing import Optional, List, Dict

from . import mixins
from .sd_objs import registration_objs
from .logger import init_root_logger

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
	UUID: str

	def __init__(self):
		self.plugin_uuid: Optional[str] = None
		self.ws: Optional[websockets.WebSocketClientProtocol] = None
		self.info: Optional[registration_objs.Info] = None


class StreamDeck(Base):
	def __init__(
			self,
			actions: Optional[List[Action]],
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

		self.actions_list: Optional[List[Action]] = actions
		self.actions: Dict[str, Action] = {}

		self.ws: Optional[websockets.WebSocketClientProtocol] = None
		self.port: Optional[int] = None
		self.plugin_uuid: Optional[str] = None
		self.register_event: Optional[str] = None
		self.info: Optional[registration_objs.Info] = None

		self.registration_dict: Optional[dict] = None

	async def run(self) -> None:
		logger.debug("Plugin has been started")

		parser = argparse.ArgumentParser(
			description="Streamdeck Plugin",
		)
		parser.add_argument('-port', dest='port', type=int, help="Port", required=True)
		parser.add_argument('-pluginUUID', dest='pluginUUID', type=str, help="PluginUUID", required=True)
		parser.add_argument('-registerEvent', dest='registerEvent', type=str, help="RegisterEvent", required=True)
		parser.add_argument('-info', dest='info', type=str, help="Info", required=True)
		args = parser.parse_args()

		self.port: int = args.port
		logger.debug(f"{self.port=}")
		self.plugin_uuid: str = args.pluginUUID
		logger.debug(f"{self.plugin_uuid=}")
		self.register_event: str = args.registerEvent
		logger.debug(f"{self.register_event=}")
		self.info: registration_objs.Info = registration_objs.Info.model_validate(json.loads(args.info))
		logger.debug(f"{self.info=}")

		self.registration_dict = {"event": self.register_event, "uuid": self.plugin_uuid}
		logger.debug(f"{self.registration_dict=}")

		# Open the websocket here.

	def __init_actions(self) -> None:
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
			self.actions[action_uuid] = action

	async def __handle_ws_message(
			self,
			message: str,
			) -> None:
		message_dict = json.loads(message)
		logger.debug(f"{message_dict=}")

		# Route the message to the appropriate handle.
		event_routing = None  # event_routings.EVENT_ROUTING_MAP.get(event)
		if event_routing is None:
			logger.warning("event_routing is None")
			return

	async def __start_ws_connection(self) -> None:
		ws_uri = f"ws://localhost:{self.port}"
		async for websocket in websockets.connect(ws_uri):
			try:
				async for message in websocket:
					await self.__handle_ws_message(message)
			except websockets.ConnectionClosed:
				continue



