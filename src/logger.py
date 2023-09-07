import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / 'logs'
LOG_FILE_NAME = 'wd_bot.log'
LOG_FORMAT = ("[%(asctime)s,%(msecs)d] %(levelname)s "
              "[%(name)s:%(lineno)s] %(message)s")
LOG_DT_FORMAT = "%d.%m.%y %H:%M:%S"
LOG_BACKUP_COUNT = 5
LOG_MAX_SIZE = 50000000


def configure_logging() -> None:
    """Configure global logging."""
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / LOG_FILE_NAME
    rotating_handler = RotatingFileHandler(
        log_file, maxBytes=LOG_MAX_SIZE, backupCount=LOG_BACKUP_COUNT
    )
    logging.basicConfig(
        datefmt=LOG_DT_FORMAT,
        format=LOG_FORMAT,
        level=logging.INFO,
        handlers=(rotating_handler, logging.StreamHandler())
    )

    # Disable information logs from telegram API itself requests.
    logging.getLogger("httpx").setLevel(logging.WARNING)
