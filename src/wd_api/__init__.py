import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

sys.path.append(str(BASE_DIR))

from constants import DEFAULT_TYPE, DNS_SERVERS, ALLOWED_RECORDS  # noqa
from wd import Domain  # noqa
from exceptions import BadDomain  # noqa