import websockets
from typing import Optional

from . import Base
from . import registration_objs
from . import StreamDeck


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
		self.instance_settings: dict[str, dict] = {}

