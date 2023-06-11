import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / 'logs'
LOG_FORMAT = "%(asctime)s - [%(levelname)s] - %(message)s"
LOG_BACKUP_COUNT = 5
LOG_MAX_SIZE = 50000000


def configure_tg_bot_logging():
    """Configure local logger for wd telegram bot."""
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / 'wd_bot.log'
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=LOG_MAX_SIZE, backupCount=LOG_BACKUP_COUNT)
    stdout_handler = logging.StreamHandler()
    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    stdout_handler.setFormatter(formatter)
    return logger
