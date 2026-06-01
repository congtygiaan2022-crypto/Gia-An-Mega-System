import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import colorlog

from modules.config_loader import CONFIG


def get_logger(name: str) -> logging.Logger:
    cfg = CONFIG["logging"]
    log_dir = os.path.dirname(cfg["file"])
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(cfg["level"])

    # Console handler — force UTF-8 on Windows to avoid cp1252 garbling
    if sys.platform == "win32":
        import io
        stream = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    else:
        stream = sys.stderr
    console = colorlog.StreamHandler(stream=stream)
    console.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        }
    ))

    # Rotating file handler
    file_handler = RotatingFileHandler(
        cfg["file"],
        maxBytes=cfg["max_bytes"],
        backupCount=cfg["backup_count"],
        encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
    ))

    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger
