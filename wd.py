import subprocess
import datetime
import re
import json
from typing import Tuple

import idna
import whois

import messages
from exceptions import BadDomain

ALLOWED_RECORDS: Tuple[str, ...] = ('TXT', 'A', 'MX', 'CNAME', 'AAAA', 'SOA',
                                    'DNAME', 'DS', 'NS', 'SRV', 'PTR', 'CAA',
                                    'TLSA')
DNS_SERVERS: str = ("8.8.8.8 1.1.1.1 ns1.hostiman.ru "
                    "ns2.hostiman.ru ns3.hostiman.com ns4.hostiman.com")
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

    def whois_json(self) -> str:
        """Make whois query and brings it to JSON output."""
        decoded_domain = domain_decode(self.domain)
        query = whois.query(self.domain)
        if query:
            if decoded_domain != self.domain:
                query.__dict__['name_IDN'] = decoded_domain
            return json.dumps(query.__dict__, default=str, ensure_ascii=False)
        return json.dumps({'message': 'Domain is not registred'})

    def dig_tg_message(self, record: str = 'A') -> str:
        """Make dig query and return telegram string message."""
        record = record.upper()
        outputlist = f'🔍 Here is DIG {domain_decode(self.domain)}:\n\n'
        if record not in ALLOWED_RECORDS:
            record = 'A'
        for server in DNS_SERVERS.split():
            temp = subprocess.run(
                ['dig', '+short', self.domain, f'@{server}', record],
                stdout=subprocess.PIPE
            )
            temp_output = temp.stdout.decode('utf-8')
            if not temp_output:
                temp_output = '- empty -\n'
            outputlist += f'▫ {record} at {server}:\n'
            outputlist += str(temp_output) + '\n'
        return outputlist

    def dig_json(self, record: str = 'A') -> str:
        """Make dig query and brings it to JSON output."""
        record = record.upper()
        if record not in ALLOWED_RECORDS:
            record = 'A'
        output = {
            'Domain': self.domain,
            'Record': record,
        }
        for server in DNS_SERVERS.split():
            temp = subprocess.run(
                ['dig', '+short', self.domain, f'@{server}', record],
                stdout=subprocess.PIPE
            )
            temp_output = temp.stdout.decode('utf-8').rstrip()
            temp_output = re.sub('"', '', temp_output)
            output[server] = temp_output.split('\n')
        return json.dumps(output)
