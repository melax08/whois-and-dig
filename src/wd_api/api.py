from fastapi import APIRouter
import whois

from .schemas import DomainDig, DomainWhois, DigSettings
from . import DEFAULT_TYPE, DNS_SERVERS, Domain, BadDomain, ALLOWED_RECORDS

router = APIRouter()


@router.get('/dig/settings', tags=['dig'], response_model=DigSettings)
def dig_settings():
    """Allows to get information about current
    DIG settings (default type and allowed records to dig)."""
    return {"default_type": DEFAULT_TYPE, "allowed_records": ALLOWED_RECORDS}


@router.post('/dig', tags=['dig'])
def dig_api(request_data: DomainDig):
    """Allows to get DIG information about domain."""
    try:
        domain = Domain(request_data.domain)
        dns = request_data.dns
        if isinstance(request_data.dns, str):
            dns = [dns]
        dig_output = domain.dig(request_data.record, dns)
        return dig_output
    except BadDomain:
        return {'message': 'Bad domain', 'result': False}


@router.post('/whois', tags=['whois'])
def whois_api(request_data: DomainWhois):
    """Allows to get WHOIS information about domain."""
    try:
        domain = Domain(request_data.domain)
        whois_output = domain.whois_json()
        return whois_output
    except BadDomain:
        return {'message': 'Bad domain', 'result': False}
    except (
            whois.exceptions.WhoisCommandFailed,
            whois.exceptions.WhoisPrivateRegistry,
            whois.exceptions.FailedParsingWhoisOutput,
            whois.exceptions.UnknownTld,
            whois.exceptions.UnknownDateFormat
    ) as error:
        return {'message': str(error), 'result': False}
