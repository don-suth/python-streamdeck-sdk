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
		self.info: Optional[registration_objs.Info]


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


