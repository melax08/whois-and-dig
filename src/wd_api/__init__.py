import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

sys.path.append(str(BASE_DIR))

from constants import DEFAULT_TYPE, DNS_SERVERS, ALLOWED_RECORDS
from wd import Domain
from exceptions import BadDomain