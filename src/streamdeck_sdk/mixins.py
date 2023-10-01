import asyncio
import json

import pydantic
import websockets
import logging

from .logger import log_errors_async
from .sd_objs import events_received_objs, events_sent_objs

from typing import Awaitable

logger = logging.getLogger()


class SendMixin:
	ws: websockets.WebSocketClientProtocol

	@log_errors_async
	async def send(
			self,
			data: dict | str | pydantic.BaseModel
			) -> None:
		"""Send data to the Streamdeck API

		Args:
			data: The data to send.
		"""
		match data:
			# Convert the data into a JSON string.
			case dict(data):
				data = json.dumps(data, ensure_ascii=False)
			case str(data):
				# Leave strings as they are.
				pass
			case basemodel if isinstance(basemodel, pydantic.BaseModel):
				data = basemodel.model_dump_json()
			case _:
				logger.error(f"Attempted to send invalid {data=}")
				return
		logger.debug(f"{data=}")
		await self.ws.send(data)


class BaseEventSendMixin(SendMixin):
	pass


class PluginEventsSendMixin(BaseEventSendMixin):
	plugin_uuid: str

	async def set_global_settings(self, payload: dict) -> None:
		"""Set the global settings. All Actions can access this setting.

		Args:
			payload: dict(JSON) of settings to set.
		"""
		message = events_sent_objs.SetGlobalSettings(
			context=self.plugin_uuid,
			payload=payload,
			)
		await self.send(message)

	async def get_global_settings(self) -> None:
		"""Get the global settings.
		"""
		message = events_sent_objs.GetGlobalSettings(
			context=self.plugin_uuid,
			)
		await self.send(message)

	async def open_url(self, url: str) -> None:
		message = events_sent_objs.OpenUrl(
			payload=events_sent_objs.OpenUrlPayload(
				url=url
				)
			)
		await self.send(message)

	async def log_message(self, message: str) -> None:
		message = events_sent_objs.LogMessage(
			payload=events_sent_objs.LogMessagePayload(
				message=message
				)
			)
		await self.send(message)

	async def switch_to_profile(
			self,
			device: str,
			profile: str,
			) -> None:
		message = events_sent_objs.SwitchToProfile(
			context=self.plugin_uuid,
			device=device,
			payload=events_sent_objs.SwitchToProfilePayload(
				profile=profile
				)
			)
		await self.send(message)


class ActionEventsSendMixin(BaseEventSendMixin):

	async def set_settings(
			self,
			context: str,
			payload: dict,
			) -> None:
		message = events_sent_objs.SetSettings(
			context=context,
			payload=payload,
			)
		await self.send(message)

	async def get_settings(
			self,
			context: str,
			) -> None:
		message = events_sent_objs.GetSettings(
			context=context,
			)
		await self.send(message)

	async def set_title(
			self,
			context: str,
			payload: events_sent_objs.SetTitlePayload,
			) -> None:
		message = events_sent_objs.SetTitle(
			context=context,
			payload=payload,
			)
		await self.send(message)

	async def set_image(
			self,
			context: str,
			payload: events_sent_objs.SetImagePayload,
			) -> None:
		message = events_sent_objs.SetImage(
			context=context,
			payload=payload,
			)
		await self.send(message)

	async def set_feedback(
			self,
			context: str,
			payload: dict,
			) -> None:
		message = events_sent_objs.SetFeedback(
			context=context,
			payload=payload,
			)
		await self.send(message)

	async def set_feedback_layout(
			self,
			context: str,
			layout: str,
			) -> None:
		message = events_sent_objs.SetFeedbackLayout(
			context=context,
			payload=events_sent_objs.SetFeedbackLayoutPayload(
				layout=layout,
				)
			)
		await self.send(message)

	async def show_alert(
			self,
			context: str,
			) -> None:
		message = events_sent_objs.ShowAlert(
			context=context,
			)
		await self.send(message)

	async def show_ok(
			self,
			context: str,
			) -> None:
		message = events_sent_objs.ShowOk(
			context=context,
			)
		await self.send(message)

	async def set_state(
			self,
			context: str,
			state: int,
			) -> None:
		message = events_sent_objs.SetState(
			context=context,
			payload=events_sent_objs.SetStatePayload(
				state=state,
				)
			)
		await self.send(message)

	async def send_to_property_inspector(
			self,
			action: str,
			context: str,
			payload: dict,
			) -> None:
		message = events_sent_objs.SendToPropertyInspector(
			action=action,
			context=context,
			payload=payload,
			)
		await self.send(message)


class BaseEventHandlerMixin:
	background_tasks: set[Awaitable] = set()

	def schedule_background_task(self, awaitable):
		task = asyncio.create_task(awaitable)
		self.background_tasks.add(task)
		task.add_done_callback(self.background_tasks.discard)


# class ActionEventHandlersMixin:
class ActionEventHandlersMixin(BaseEventHandlerMixin):
	async def _on_did_receive_settings(self, obj: events_received_objs.DidReceiveSettings) -> None:
		await self.on_did_receive_settings(obj=obj)

	async def _on_key_down(self, obj: events_received_objs.KeyDown) -> None:
		logger.debug("sending from _on_key_down to self.on_key_down")  # TODO: Remove
		# await self.on_key_down(obj=obj)
		self.schedule_background_task(self.on_key_down(obj=obj))

	async def _on_key_up(self, obj: events_received_objs.KeyUp) -> None:
		logger.debug("sending from _on_key_up to self.on_key_up")  # TODO: Remove
		# await self.on_key_up(obj=obj)
		self.schedule_background_task(self.on_key_up(obj=obj))

	async def _on_touch_tap(self, obj: events_received_objs.TouchTap) -> None:
		await self.on_touch_tap(obj=obj)

	async def _on_dial_down(self, obj: events_received_objs.DialDown) -> None:
		await self.on_dial_down(obj=obj)

	async def _on_dial_up(self, obj: events_received_objs.DialUp) -> None:
		await self.on_dial_up(obj=obj)

	async def _on_dial_press(self, obj: events_received_objs.DialPress) -> None:
		await self.on_dial_press(obj=obj)

	async def _on_dial_rotate(self, obj: events_received_objs.DialRotate) -> None:
		await self.on_dial_rotate(obj=obj)

	async def _on_will_appear(self, obj: events_received_objs.WillAppear) -> None:
		await self.on_will_appear(obj=obj)

	async def _on_will_disappear(self, obj: events_received_objs.WillDisappear) -> None:
		await self.on_will_disappear(obj=obj)

	async def _on_title_parameters_did_change(self, obj: events_received_objs.TitleParametersDidChange) -> None:
		await self.on_title_parameters_did_change(obj=obj)

	async def _on_property_inspector_did_appear(self, obj: events_received_objs.PropertyInspectorDidAppear) -> None:
		await self.on_property_inspector_did_appear(obj=obj)

	async def _on_property_inspector_did_disappear(self, obj: events_received_objs.PropertyInspectorDidDisappear) -> None:
		await self.on_property_inspector_did_disappear(obj=obj)

	async def _on_send_to_plugin(self, obj: events_received_objs.SendToPlugin) -> None:
		await self.on_send_to_plugin(obj=obj)

	async def _on_send_to_property_inspector(self, obj: events_received_objs.SendToPropertyInspector) -> None:
		await self.on_send_to_property_inspector(obj=obj)

	async def on_did_receive_settings(self, obj: events_received_objs.DidReceiveSettings) -> None:
		pass

	async def on_key_down(self, obj: events_received_objs.KeyDown) -> None:
		logger.debug("on_key_down: I should be overwritten")  # TODO: Remove
		pass

	async def on_key_up(self, obj: events_received_objs.KeyUp) -> None:
		logger.debug("on_key_up: I should be overwritten")  # TODO: Remove
		pass

	async def on_touch_tap(self, obj: events_received_objs.TouchTap) -> None:
		pass

	async def on_dial_down(self, obj: events_received_objs.DialDown) -> None:
		pass

	async def on_dial_up(self, obj: events_received_objs.DialUp) -> None:
		pass

	async def on_dial_press(self, obj: events_received_objs.DialPress) -> None:
		pass

	async def on_dial_rotate(self, obj: events_received_objs.DialRotate) -> None:
		pass

	async def on_will_appear(self, obj: events_received_objs.WillAppear) -> None:
		pass

	async def on_will_disappear(self, obj: events_received_objs.WillDisappear) -> None:
		pass

	async def on_title_parameters_did_change(self, obj: events_received_objs.TitleParametersDidChange) -> None:
		pass

	async def on_property_inspector_did_appear(self, obj: events_received_objs.PropertyInspectorDidAppear) -> None:
		pass

	async def on_property_inspector_did_disappear(self, obj: events_received_objs.PropertyInspectorDidDisappear) -> None:
		pass

	async def on_send_to_plugin(self, obj: events_received_objs.SendToPlugin) -> None:
		pass

	async def on_send_to_property_inspector(self, obj: events_received_objs.SendToPropertyInspector) -> None:
		pass


class PluginEventHandlersMixin(BaseEventHandlerMixin):
	async def _on_did_receive_global_settings(self, obj: events_received_objs.DidReceiveGlobalSettings) -> None:
		await self.on_did_receive_global_settings(obj=obj)

	async def _on_device_did_connect(self, obj: events_received_objs.DeviceDidConnect) -> None:
		await self.on_device_did_connect(obj=obj)

	async def _on_device_did_disconnect(self, obj: events_received_objs.DeviceDidDisconnect) -> None:
		await self.on_device_did_disconnect(obj=obj)

	async def _on_application_did_launch(self, obj: events_received_objs.ApplicationDidLaunch) -> None:
		await self.on_application_did_launch(obj=obj)

	async def _on_application_did_terminate(self, obj: events_received_objs.ApplicationDidTerminate) -> None:
		await self.on_application_did_terminate(obj=obj)

	async def _on_system_did_wake_up(self, obj: events_received_objs.SystemDidWakeUp) -> None:
		await self.on_system_did_wake_up(obj=obj)

	async def on_did_receive_global_settings(self, obj: events_received_objs.DidReceiveGlobalSettings) -> None:
		pass

	async def on_device_did_connect(self, obj: events_received_objs.DeviceDidConnect) -> None:
		pass

	async def on_device_did_disconnect(self, obj: events_received_objs.DeviceDidDisconnect) -> None:
		pass

	async def on_application_did_launch(self, obj: events_received_objs.ApplicationDidLaunch) -> None:
		pass

	async def on_application_did_terminate(self, obj: events_received_objs.ApplicationDidTerminate) -> None:
		pass

	async def on_system_did_wake_up(self, obj: events_received_objs.SystemDidWakeUp) -> None:
		pass


class ExtraKeyEventHandlersMixin(ActionEventHandlersMixin):
	long_press_delay: float = 0.8
	double_press_delay: float = 0.5
	last_key_down_event: dict[str, asyncio.Future] = {}
	#last_key_down_time: dict[str, float] = {}
	#last_key_up_event: dict[str, asyncio.Future] = {}
	last_key_up_time: dict[str, float] = {}
	should_skip_key_up: dict[str, bool] = {}
	# latest_key_events: dict[str, tuple[float, bool]] = dict()

	async def _on_key_down(self, obj: events_received_objs.KeyDown) -> None:
		logger.debug("extra _on_key_down triggered")  # TODO: Remove
		# Intercept the normal KeyDown event, and start timing.
		context = obj.context
		loop = asyncio.get_running_loop()
		#time_start = loop.time()

		if self.long_press_delay > 0:
			#self.last_key_down_time[context] = time_start
			self.last_key_down_event[context] = loop.create_future()

			try:
				# Wait until a KeyUp event happens, or until we reach the long press delay.
				logger.debug("Begin waiting for a KeyUp")
				await asyncio.wait_for(self.last_key_down_event[context], self.long_press_delay)
				# At this point, a KeyUp was received.
				logger.debug("A KeyUp was received: Cancel the on_long_press")
			except TimeoutError:
				# At this point, it is a long press.
				# Skip the next KeyUp, and call LongPress.
				logger.debug("KeyUp not detected: Long Press")
				self.should_skip_key_up[context] = True
				# await self.on_key_long_press(obj=obj)
				self.schedule_background_task(self.on_key_long_press(obj=obj))

			# while True:
			# 	# Check back every 100ms.
			# 	await asyncio.sleep(0.1)
			# 	time_now = loop.time()
			# 	logger.debug(f"{time_now=}, {time_start=}")  # TODO: Remove
			#
			# 	# Check the latest key-press. If it is newer, then
			# 	# the key has been released, and we can stop checking.
			# 	latest_event = self.latest_key_events.get(context, None)
			# 	logger.debug(f"{latest_event[0]=}, {latest_event[1]=}")  # TODO: Remove
			# 	if latest_event is not None:
			# 		if latest_event[0] > time_start:
			# 			break
			#
			# 	# If the time is over the long press time, then
			# 	# we tell the action to ignore the next KeyUp event.
			# 	elapsed_time = time_now - time_start
			# 	logger.debug(f"{elapsed_time=}")  # TODO: Remove
			# 	if elapsed_time >= self.long_press_delay:
			# 		self.latest_key_events[context] = (time_now, True)
			# 		await self.on_key_long_press(obj=obj)
			# 		return

	async def _on_key_up(self, obj: events_received_objs.KeyUp) -> None:
		logger.debug("extra _on_key_up triggered")  # TODO: Remove
		context: str = obj.context
		if self.last_key_down_event[context] is not None and not self.last_key_down_event[context].done():
			logger.debug("Setting the result of the Future to cancel the LongPress.")
			self.last_key_down_event[context].set_result(True)
		# Intercept the normal KeyUp event.
		loop = asyncio.get_running_loop()
		should_skip: bool = self.should_skip_key_up.get(context, False)
		is_double_press: bool = False

		time_now = loop.time()
		time_of_last_event = self.last_key_up_time.get(context, None)

		if time_of_last_event is not None:
			elapsed_time: float = time_now - time_of_last_event
			logger.debug(f"{time_now=} - {time_of_last_event= } = {elapsed_time=}")
			if elapsed_time <= self.double_press_delay:
				logger.debug("This is a double press!")
				is_double_press = True


		self.should_skip_key_up[context] = False

		if should_skip:
			logger.debug("Skipping KeyUp after a keyhold")
		else:
			self.last_key_up_time[context] = time_now
			logger.debug("Not skipping KeyUp")
			if is_double_press:
				logger.debug("Double Press!")
				# await self.on_key_double_press(obj=obj)
				self.schedule_background_task(self.on_key_double_press(obj=obj))
			else:
				logger.debug("Regular press")
				# await self.on_key_up(obj=obj)
				self.schedule_background_task(self.on_key_up(obj=obj))


		# # Check the last event to see if we should skip this one.
		# if latest_event is not None:
		# 	last_key_time, should_skip = latest_event
		# 	elapsed_time = time_now - last_key_time
		# 	# If not, check if the last event happened quickly enough.
		# 	# If so, it's a double press.
		# 	if elapsed_time < self.double_press_delay:
		# 		is_double_press = True
		#
		# self.latest_key_events[context] = (time_now, False)
		# logger.debug(f"{should_skip=}")  # TODO: Remove
		# if not should_skip:
		# 	if is_double_press:
		# 		logger.debug("double press!")  # TODO: Remove
		# 		await self.on_key_double_press(obj=obj)
		# 	else:
		# 		logger.debug("regular key up")  # TODO: Remove
		# 		await self.on_key_up(obj=obj)
		# else:
		# 	logger.debug("Skipping")  # TODO: Remove

	async def on_key_long_press(self, obj):
		logger.debug("on_key_long_press: I should be overwritten")  # TODO: Remove
		pass

	async def on_key_double_press(self, obj):
		logger.debug("on_key_double_press: I should be overwritten")  # TODO: Remove
		pass
