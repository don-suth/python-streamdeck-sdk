import argparse
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Callable, Awaitable

import pydantic
import websockets

from . import event_routings
from . import mixins
from .logger import init_root_logger, log_errors_async, rename_plugin_logger
from .sd_objs import registration_objs

logger = logging.getLogger(__name__)






