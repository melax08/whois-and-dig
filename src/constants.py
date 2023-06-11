import os
from typing import Tuple, List

from dotenv import load_dotenv

load_dotenv()

TOKEN: str = os.getenv('TOKEN')
DNS_SERVERS: List[str] = os.getenv(
    'DNS_SERVERS', default='8.8.8.8 1.1.1.1').split()
ALLOWED_RECORDS: Tuple[str, ...] = ('TXT', 'A', 'MX', 'CNAME', 'AAAA', 'SOA',
                                    'DNAME', 'DS', 'NS', 'SRV', 'PTR', 'CAA',
                                    'TLSA')
DEFAULT_TYPE: str = 'A'
LJ_VALUE: int = 20

# Max callback_data len is 64 bytes (len of domain + ' CNAME' should be <= 64).
# https://core.telegram.org/bots/api#inlinekeyboardbutton
MAX_DOMAIN_LEN_TO_BUTTONS = 58
