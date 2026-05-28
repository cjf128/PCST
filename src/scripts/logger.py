# Copyright (c) 2026 PCViewer Jinfr
import logging
import sys
import time
from pathlib import Path

from path import LOGS_PATH

_logger = None

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_LOG_FILES = 7


def _cleanup_old_logs(log_dir: Path, max_logs: int = MAX_LOG_FILES):
    log_files = sorted(log_dir.glob("viewer_*.log"), key=lambda f: f.stat().st_mtime)
    for old_file in log_files[:-max_logs]:
        old_file.unlink()


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


def setup_logger(log_dir=None, name="Viewer"):
    global _logger

    if _logger is not None:
        return _logger

    log_dir = log_dir or LOGS_PATH
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"viewer_{timestamp}.log"

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
