import logging
import os
import sys
from logging.handlers import RotatingFileHandler
import threading

import colorlog

from modules.config_loader import CONFIG

_shared_handlers = []
_log_lock = threading.Lock()


class SafeRotatingFileHandler(RotatingFileHandler):
    def doRollover(self):
        try:
            super().doRollover()
        except OSError:
            # If the file is locked by another process (e.g. GUI and CLI running concurrently),
            # we catch the exception and ensure the stream is reopened in append mode.
            if not self.delay and self.stream is None:
                self.stream = self._open()


def get_logger(name: str) -> logging.Logger:
    global _shared_handlers

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    cfg = CONFIG["logging"]
    logger.setLevel(cfg["level"])
    logger.propagate = False

    with _log_lock:
        if not _shared_handlers:
            log_dir = os.path.dirname(cfg["file"])
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

            # Console handler — force UTF-8 on Windows to avoid cp1252 garbling
            if sys.platform == "win32":
                import io
                stream = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
            else:
                stream = sys.stderr
            console = colorlog.StreamHandler(stream=stream)
            console.setFormatter(colorlog.ColoredFormatter(
                "%(log_color)s[%(asctime)s] %(levelname)s %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                }
            ))

            # Rotating file handler
            file_handler = SafeRotatingFileHandler(
                cfg["file"],
                maxBytes=cfg["max_bytes"],
                backupCount=cfg["backup_count"],
                encoding="utf-8"
            )
            file_handler.setFormatter(logging.Formatter(
                "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))

            _shared_handlers = [console, file_handler]

        for h in _shared_handlers:
            if h not in logger.handlers:
                logger.addHandler(h)

    return logger
