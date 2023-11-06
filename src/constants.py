import os
from typing import Tuple

from dotenv import load_dotenv

load_dotenv()

# WD Constants

DNS_SERVERS: Tuple[str] = tuple(os.getenv(
    'DNS_SERVERS', default='8.8.8.8 1.1.1.1').split())

ALLOWED_RECORDS: Tuple[str] = tuple(os.getenv(
    'ALLOWED_RECORDS',
    default='TXT A MX CNAME AAAA SOA DNAME DS NS SRV PTR CAA TLSA'
).split())

DEFAULT_TYPE: str = os.getenv('DEFAULT_TYPE', default='A')

RECORDS_ON_KEYBOARD: Tuple[str, ...] = (
    'A', 'AAAA', 'CNAME', 'TXT', 'MX', 'SOA'
)

DIG_TIMEOUT: int = 3

SHELL_OUTPUT_ENCODING: str = 'utf-8'

# Telegram bot constants

TOKEN: str = os.getenv('TOKEN')

# Max callback_data len is 64 bytes (len of domain + ' CNAME' should be <= 64).
# https://core.telegram.org/bots/api#inlinekeyboardbutton
MAX_DOMAIN_LEN_TO_BUTTONS: int = 58
