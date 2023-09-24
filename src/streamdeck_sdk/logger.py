import logging
import inspect
from logging.handlers import RotatingFileHandler

from pathlib import Path

from decohints import decohints

from functools import wraps, update_wrapper

_root_logger: logging.Logger = logging.getLogger()
_log_errors_decorator_logger = logging.getLogger("log_errors_decorator")

logger = logging.getLogger("streamdeck_plugin")


def init_root_logger(
		log_file: Path,
		log_level: int = logging.DEBUG,
		log_max_bytes: int = 3 * 1024 * 1024,  # eg. 3 MB maximum
		log_backup_count: int = 2,
		) -> None:
	_root_logger.setLevel(log_level)
	logs_dir: Path = log_file.parent
	logs_dir.mkdir(parents=True, exist_ok=True)

	formatter = logging.Formatter(
		"%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d): %(message)s",
		)

	rfh = RotatingFileHandler(
		log_file,
		mode="a",
		maxBytes=log_max_bytes,
		backupCount=log_backup_count,
		encoding="utf-8",
		delay=False,
		)
	rfh.setLevel(log_level)
	rfh.setFormatter(formatter)
	_root_logger.addHandler(rfh)


def log_errors(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		try:
			result = func(*args, **kwargs)
		except BaseException as err:
			_log_errors_decorator_logger.error(str(err), exc_info=True)
			return
		return result
	wrapper: func
	return wrapper


def log_errors_async(func):
	@wraps(func)
	async def wrapper(*args, **kwargs):
		try:
			result = await func(*args, **kwargs)
		except BaseException as err:
			_log_errors_decorator_logger.error(str(err), exc_info=True)
			return
		return result
	wrapper: func
	return wrapper
