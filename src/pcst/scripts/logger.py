# Copyright (c) 2026 PCST Jinfr
import logging
import sys
import time
from threading import RLock
from pathlib import Path

from pcst.path import LOGS_PATH

_logger = None
_logger_lock = RLock()

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_LOG_FILES = 7


def _cleanup_old_logs(log_dir: Path, max_logs: int = MAX_LOG_FILES):
    log_files = sorted(log_dir.glob("pcst_*.log"), key=lambda f: f.stat().st_mtime)
    for old_file in log_files[:-max_logs]:
        try:
            old_file.unlink()
        except OSError:
            # On Windows another process/thread may still have a handle to a
            # just-created log.  Failure to remove an old log must never crash
            # a worker thread or prevent the application from starting.
            continue


def _create_file_handler(log_file: Path) -> logging.FileHandler:
    handler = logging.FileHandler(str(log_file), encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    return handler


def _create_stream_handler() -> logging.StreamHandler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    return handler


def setup_logger(log_dir=None, name="PCST"):
    global _logger

    with _logger_lock:
        if _logger is not None:
            return _logger

        log_dir = log_dir or LOGS_PATH
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"pcst_{timestamp}.log"

        _logger = logging.getLogger(name)
        _logger.setLevel(logging.DEBUG)
        _logger.addHandler(_create_file_handler(log_file))
        _logger.addHandler(_create_stream_handler())

        _cleanup_old_logs(log_dir)

        return _logger


def get_logger():
    if _logger is None:
        return setup_logger()
    return _logger


def log_info(message: str):
    get_logger().info(message)


def log_debug(message: str):
    get_logger().debug(message)


def log_warning(message: str):
    get_logger().warning(message)


def log_error(message: str):
    get_logger().error(message)
