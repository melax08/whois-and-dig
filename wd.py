import subprocess
import datetime
import re
import os
from typing import List, Tuple

import idna
import whois
from dotenv import load_dotenv

import messages
from exceptions import BadDomain

load_dotenv()

ALLOWED_RECORDS: Tuple[str, ...] = ('TXT', 'A', 'MX', 'CNAME', 'AAAA', 'SOA',
                                    'DNAME', 'DS', 'NS', 'SRV', 'PTR', 'CAA',
                                    'TLSA')
DEFAULT_TYPE: str = 'A'
DNS_SERVERS: List[str] = os.getenv(
    'DNS_SERVERS', default='8.8.8.8 1.1.1.1').split()
LJ_VALUE: int = 20


def domain_encode(domain: str) -> str:
    """Encode domain from IDN to punycode."""
    try:
        domain = idna.encode(domain)
    except idna.core.InvalidCodepoint:
        return domain
    return domain.decode()


def domain_decode(domain: str) -> str:
    """Decode domain from punycode to IDN."""
    try:
        domain = idna.decode(domain)
    except idna.core.InvalidCodepoint:
        return domain
    return domain


class Domain:
    """The Domain class receive a raw URL, link, domain or whatever
    then find domain name with regexp and allow to use various methods to get
    information about domain.
    """

    def __init__(self, raw_site: str) -> None:
        self.raw_site = raw_site
        self.domain = self.domain_getter()

    def domain_getter(self) -> str:
        """Lookup for domain in string and return it."""
        domain = self.raw_site.lower()
        domain = re.search(r'[.\w-]+\.[\w-]{2,}', domain)
        if domain:
            domain = domain.group(0)
            domain = domain_encode(domain)
            return domain
        else:
            raise BadDomain(messages.bad_domain)

    def whois_tg_message(self) -> str:
        """Make whois query and brings the output to string
        which can be sent as a message to telegram.
        """
        decoded_domain = domain_decode(self.domain)
        query = whois.query(self.domain)
        if query:
            whois_information = '🔍 Here is whois information:'
            if decoded_domain != self.domain:
                whois_information += ('\nPunycode: '.ljust(LJ_VALUE)
                                      + f'<code>{query.name}</code>')
            whois_information += ('\nDomain: '.ljust(LJ_VALUE)
                                  + domain_decode(query.name))
            for ns in query.name_servers:
                whois_information += '\nNserver: '.ljust(LJ_VALUE) + ns
            if query.registrar:
                whois_information += ('\nRegistrar: '.ljust(LJ_VALUE)
                                      + query.registrar)
            if query.creation_date:
                whois_information += ('\nCreated: '.ljust(LJ_VALUE)
                                      + str(query.creation_date))
            if query.expiration_date:
                if datetime.datetime.utcnow() < query.expiration_date:
                    whois_information += ('\nExpires: '.ljust(LJ_VALUE)
                                          + str(query.expiration_date)
                                          + ' - active!')
                else:
                    whois_information += ('\nExpires: '.ljust(LJ_VALUE)
                                          + str(query.expiration_date)
                                          + '<b> - EXPIRED! 🛑</b>')
            return whois_information
        else:
            return messages.domain_not_registred

    def whois_json(self) -> dict:
        """Make whois query and brings it to JSON output."""
        decoded_domain = domain_decode(self.domain)
        query = whois.query(self.domain)
        if query:
            query.result = True
            if decoded_domain != self.domain:
                query.name_IDN = decoded_domain
            else:
                query.name_IDN = None
            if query.expiration_date:
                if datetime.datetime.utcnow() < query.expiration_date:
                    query.is_active = True
                else:
                    query.is_active = False
                query.expiration_date = int(query.expiration_date.timestamp())
            else:
                query.is_active = None
            if query.creation_date:
                query.creation_date = int(query.creation_date.timestamp())
            return query.__dict__
        return {'result': False}

    def dig(self, record: str = DEFAULT_TYPE, ns_list: tuple = DNS_SERVERS
            ) -> dict:
        """Main dig method, Returns information
        about the specified entry on the specified name servers.
        """
        if record:
            record = record.upper()
        if record not in ALLOWED_RECORDS:
            record = DEFAULT_TYPE
        output = {
            'domain': self.domain,
            'record': record,
            'result': True,
            'data': {}
        }
        for server in ns_list:
            output['data'][server] = []
            temp = subprocess.run(
                [
                    'dig',
                    '+noall',
                    '+answer',
                    self.domain,
                    f'@{server}',
                    record,
                    '+timeout=3'
                ],
                stdout=subprocess.PIPE
            )
            temp_output = temp.stdout.decode('utf-8')
            temp_output = re.sub('"', '', temp_output)
            for result in temp_output.splitlines():
                query = result.split(maxsplit=4)
                new_result = {
                    'ttl': query[1],
                    'content': query[4]
                }
                output['data'][server].append(new_result)
        return output

    def dig_tg_message(self, record: str = DEFAULT_TYPE) -> str:
        dig_output = self.dig(record=record)
        domain = dig_output.pop('domain')
        record = dig_output.pop('record')
        message = f'🔍 Here is DIG {domain}:\n\n'
        for ns, results in dig_output['data'].items():
            message += f'▫ {record} at {ns}:\n'
            if results:
                for result in results:
                    content = result.get('content')
                    message += content + '\n'
                message += '\n'
            else:
                message += '- empty -\n\n'
        return message
