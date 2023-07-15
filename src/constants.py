import os
from typing import List

from dotenv import load_dotenv

load_dotenv()

TOKEN: str = os.getenv('TOKEN')
DNS_SERVERS: List[str] = os.getenv(
    'DNS_SERVERS', default='8.8.8.8 1.1.1.1').split()
ALLOWED_RECORDS: List[str] = os.getenv(
    'ALLOWED_RECORDS',
    default='TXT A MX CNAME AAAA SOA DNAME DS NS SRV PTR CAA TLSA'
).split()
DEFAULT_TYPE: str = os.getenv('DEFAULT_TYPE', default='A')

# Max callback_data len is 64 bytes (len of domain + ' CNAME' should be <= 64).
# https://core.telegram.org/bots/api#inlinekeyboardbutton
MAX_DOMAIN_LEN_TO_BUTTONS = 58
