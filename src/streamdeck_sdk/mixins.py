import json

import pydantic
import websockets
import logging

from .logger import log_errors_async
from .sd_objs import events_received_objs, events_sent_objs

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
	pass


# class ActionEventHandlersMixin:
class ActionEventHandlersMixin(BaseEventHandlerMixin):
	async def on_did_receive_settings(self, obj: events_received_objs.DidReceiveSettings) -> None:
		pass

	async def on_key_down(self, obj: events_received_objs.KeyDown) -> None:
		pass

	async def on_key_up(self, obj: events_received_objs.KeyUp) -> None:
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
