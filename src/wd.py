import subprocess
import datetime
import re
from typing import Union

import idna
import whois

import messages
from exceptions import BadDomain
from constants import ALLOWED_RECORDS, DEFAULT_TYPE, DNS_SERVERS, LJ_VALUE


class Domain:
    """The Domain class receive a raw URL, link, domain or whatever
    then find domain name with regexp and allow to use various methods to get
    information about domain.
    """

    def __init__(self, raw_site: str) -> None:
        self.raw_site = raw_site
        self.domain = self.domain_getter()

    def __str__(self):
        return self.domain

    def domain_getter(self) -> str:
        """Lookup for domain in string and return it."""
        domain = self.raw_site.lower()
        domain = re.search(r'[.\w-]+\.[\w-]{2,}', domain)
        if domain:
            domain = domain.group(0)
            domain = self.domain_encode(domain)
            return domain
        else:
            raise BadDomain(messages.bad_domain)

    def whois_tg_message(self) -> str:
        """Make whois query and brings the output to string
        which can be sent as a message to telegram.
        """
        decoded_domain = self.domain_decode(self.domain)
        query = whois.query(self.domain, force=True)
        if query:
            whois_information = ['🔍 Here is whois information:']
            if decoded_domain != self.domain:
                whois_information.append('Punycode: '.ljust(LJ_VALUE)
                                         + f'<code>{query.name}</code>')
            whois_information.append('Domain: '.ljust(LJ_VALUE)
                                     + self.domain_decode(query.name))
            for ns in query.name_servers:
                whois_information.append('Nserver: '.ljust(LJ_VALUE) + ns)
            if query.registrar:
                whois_information.append('Registrar: '.ljust(LJ_VALUE)
                                         + query.registrar)
            if query.creation_date:
                whois_information.append('Created: '.ljust(LJ_VALUE)
                                         + str(query.creation_date))
            if query.expiration_date:
                if datetime.datetime.utcnow() < query.expiration_date:
                    whois_information.append('Expires: '.ljust(LJ_VALUE)
                                             + str(query.expiration_date)
                                             + ' - active!')
                else:
                    whois_information.append('Expires: '.ljust(LJ_VALUE)
                                             + str(query.expiration_date)
                                             + '<b> - EXPIRED! 🛑</b>')
            return '\n'.join(whois_information)
        else:
            return messages.domain_not_registred

    def whois_json(self) -> dict:
        """Make whois query and brings it to JSON output."""
        decoded_domain = self.domain_decode(self.domain)
        query = whois.query(self.domain, force=True)
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

    def dig(self, record: str = DEFAULT_TYPE,
            ns_list: Union[tuple, list] = DNS_SERVERS) -> dict:
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
        message = [f'🔍 Here is DIG {domain}:']
        for ns, results in dig_output['data'].items():
            message.append(f'\n▫ {record} at {ns}:')
            if results:
                for result in results:
                    content = result.get('content')
                    message.append(content)
            else:
                message.append('- empty -')
        return '\n'.join(message)

    @staticmethod
    def domain_encode(domain: str) -> str:
        """Encode domain from IDN to punycode."""
        try:
            domain = idna.encode(domain)
        except idna.core.InvalidCodepoint:
            return domain
        return domain.decode()

    @staticmethod
    def domain_decode(domain: str) -> str:
        """Decode domain from punycode to IDN."""
        try:
            domain = idna.decode(domain)
        except idna.core.InvalidCodepoint:
            return domain
        return domain
