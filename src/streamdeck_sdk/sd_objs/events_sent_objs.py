from typing import Optional

from pydantic import BaseModel


# region NestedModels
class OpenUrlPayload(BaseModel):
	"""Payload for the openUrl event.

	Attributes:
		url: An URL to open in the default browser.
	"""
	url: str


class LogMessagePayload(BaseModel):
	"""Payload for the logMessage event.

	Attributes:
		message: A string to write to the logs file.
	"""
	message: str


class SetTitlePayload(BaseModel):
	"""Payload for the setTitle event.

	Attributes:
		title: The title to display. If there is no title parameter, the title is reset to the title set by the user.
		target: Specify if you want to display the title on the
			hardware and software (0), only on the hardware (1), or only on the software (2).
			Default is 0.
		state: A 0-based integer value representing the state of an action with multiple states.
			If not specified, the title is set to all states.
	"""
	title: str
	target: int
	state: Optional[int] = None


class SetImagePayload(BaseModel):
	"""Payload for the setImage event.

	Attributes:
		image: The image to display encoded in base64 with the image format declared in the mime type (PNG, JPEG, BMP, ...).
			svg is also supported. If not provided, the image is reset to the default image from the manifest.
			Example value: ``data:image/png;base64,iVBORw0KGgoA...``
		target: Specify if you want to display the title on the
			hardware and software (0), only on the hardware (1), or only on the software (2).
			Default is 0.
		state: A 0-based integer value representing the state of an action with multiple states.
			If not specified, the image is set to all states.
	"""
	image: str  # base64
	target: int
	state: Optional[int] = None


class SetStatePayload(BaseModel):
	"""Payload for the setState event.

	Attributes:
		state: A 0-based integer value representing the state requested.
	"""
	state: int


class SwitchToProfilePayload(BaseModel):
	"""Payload for the switchToProfile event.

	Attributes:
		profile: The name of the profile to switch to.
			The name should be identical to the name provided in the manifest.json file.
	"""
	profile: str


class SetFeedbackLayoutPayload(BaseModel):
	"""Payload for the setFeedback event.

	Attributes:
		layout: A predefined layout identifier or the relative path to a json file that contains a custom layout
	"""
	layout: str


# endregion NestedModels

# region Models
class SetSettings(BaseModel):
	context: str
	payload: dict
	event: str = "setSettings"


class GetSettings(BaseModel):
	context: str
	event: str = "getSettings"


class SetGlobalSettings(BaseModel):
	context: str
	payload: dict
	event: str = "setGlobalSettings"


class GetGlobalSettings(BaseModel):
	context: str
	event: str = "getGlobalSettings"


class OpenUrl(BaseModel):
	payload: OpenUrlPayload
	event: str = "openUrl"


class LogMessage(BaseModel):
	payload: LogMessagePayload
	event: str = "logMessage"


class SetTitle(BaseModel):
	context: str
	payload: SetTitlePayload
	event: str = "setTitle"


class SetImage(BaseModel):
	context: str
	payload: SetImagePayload
	event: str = "setImage"


class SetFeedback(BaseModel):
	context: str
	payload: dict
	event: str = "setFeedback"


class SetFeedbackLayout(BaseModel):
	context: str
	payload: SetFeedbackLayoutPayload
	event: str = "setFeedbackLayout"


class ShowAlert(BaseModel):
	context: str
	event: str = "showAlert"


class ShowOk(BaseModel):
	context: str
	event: str = "showOk"


class SetState(BaseModel):
	context: str
	payload: SetStatePayload
	event: str = "setState"


class SwitchToProfile(BaseModel):
	device: str
	context: str
	payload: SwitchToProfilePayload
	event: str = "switchToProfile"


class SendToPropertyInspector(BaseModel):
	action: str
	context: str
	payload: dict
	event: str = "sendToPropertyInspector"


class SendToPlugin(BaseModel):
	action: str
	context: str
	payload: dict
	event: str = "sendToPlugin"

# endregion Models
