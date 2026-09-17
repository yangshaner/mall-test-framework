# common/utils/logger.py

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

def get_logger(name: str = None, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name or __name__)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper()))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s)',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        LOG_DIR / 'test.log',
        maxBytes=10 * 1024 * 1024, # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger

def set_log_level(level: str):
    logging.getLogger().setLevel(getattr(logging, level.upper()))