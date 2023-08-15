from typing import Union, List

from pydantic import BaseModel

from . import DEFAULT_TYPE, DNS_SERVERS


class DigSettings(BaseModel):
    """Schema for get dig settings."""
    default_type: str = DEFAULT_TYPE
    allowed_records: List[str] = DNS_SERVERS


class DomainWhois(BaseModel):
    """Schema for get whois information about specified domain."""
    domain: str

    class Config:
        json_schema_extra = {
            'example': {
                'domain': 'google.com'
            }
        }


class DomainDig(DomainWhois):
    """Schema for get dig information about specified domain.
    Not required fields: record, dns.
    """
    record: str = DEFAULT_TYPE
    dns: Union[str, List[str]] = DNS_SERVERS

    class Config:
        json_schema_extra = {
            'example': {
                'domain': 'google.com',
                'record': 'A',
                'dns': ['1.1.1.1', '8.8.8.8']
            }
        }
