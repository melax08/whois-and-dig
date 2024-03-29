import asyncio
import datetime
import re
from typing import Tuple

import idna
import whois

import messages
from exceptions import BadDomain
from constants import (ALLOWED_RECORDS, DEFAULT_TYPE, DNS_SERVERS, DIG_TIMEOUT,
                       SHELL_OUTPUT_ENCODING)


class Domain:
    """
    The Domain class receives a raw URL, link, domain or whatever, then
    extracts the domain name from it using regexp. After this, allows to use
    various methods to get the information about extracted domain.
    """
    DOMAIN_REGEXP: str = r'[.\w-]+\.[\w-]{2,}'
    DIG_QUERY_COLUMN: int = 4

    def __init__(self, raw_site: str) -> None:
        self.domain = raw_site

    def __str__(self):
        return self.domain

    @property
    def domain(self) -> str:
        return self.__domain

    @domain.setter
    def domain(self, input_site: str) -> None:
        """Lookup for domain name in inputted string, raise the `BadDomain`
        exception if no domain in the string."""
        domain = input_site.lower()
        domain = re.search(self.DOMAIN_REGEXP, domain)

        if not domain:
            raise BadDomain(messages.BAD_DOMAIN)

        self.__domain = self.domain_encode(domain.group())

    def whois_tg_message(self) -> str:
        """Gets whois information about domain, then creates the telegram
        message with this information."""
        decoded_domain = self.domain_decode(self.domain)
        query = whois.query(self.domain, force=True)

        if not query:
            return messages.DOMAIN_NOT_REGISTERED

        whois_information = [messages.WHOIS_TG_LABEL]

        if decoded_domain != self.domain:
            whois_information.append(messages.WHOIS_ITEM.format(
                messages.PUNYCODE, f'<code>{self.domain}</code>'))

        whois_information.append(messages.WHOIS_ITEM.format(
            messages.DOMAIN, self.domain_decode(query.name)))

        whois_information.extend(
            [messages.WHOIS_ITEM.format(messages.NAMESERVER, ns)
             for ns in query.name_servers]
        )

        if query.registrar:
            whois_information.append(messages.WHOIS_ITEM.format(
                messages.REGISTRAR, query.registrar))

        if query.creation_date:
            whois_information.append(messages.WHOIS_ITEM.format(
                messages.CREATED, query.creation_date))

        if query.expiration_date:
            expiration_string = messages.WHOIS_ITEM.format(
                messages.EXPIRES, query.expiration_date)
            if datetime.datetime.utcnow() < query.expiration_date:
                expiration_string += messages.ACTIVE
            else:
                expiration_string += messages.EXPIRED
            whois_information.append(expiration_string)

        if query.status:
            whois_information.append(messages.WHOIS_ITEM.format(
                messages.STATUSES, query.status))

        return '\n'.join(whois_information)

    def whois_json(self) -> dict:
        """Makes whois query and brings it to the JSON format output."""
        decoded_domain = self.domain_decode(self.domain)
        query = whois.query(self.domain, force=True)

        if not query:
            return {
                'result': False,
                'message': messages.NO_QUERY,
            }

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

    async def _dig_task(self, server: str, record: str, output: dict):
        """Coroutine for dig request to specified DNS-server."""
        output['data'][server] = []
        proc = await asyncio.create_subprocess_exec(
            'dig',
            '+noall',
            '+answer',
            self.domain,
            f'@{server}',
            record,
            f'+timeout={DIG_TIMEOUT}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        temp_output = stdout.decode(SHELL_OUTPUT_ENCODING)
        temp_output = re.sub('"', '', temp_output)
        for result in temp_output.splitlines():
            query = result.split(maxsplit=self.DIG_QUERY_COLUMN)
            new_result = {
                'ttl': query[1],
                'content': query[4]
            }
            output['data'][server].append(new_result)

    async def dig(
            self, record: str = DEFAULT_TYPE, ns_list: Tuple[str] = DNS_SERVERS
    ) -> dict:
        """Main dig coroutine. Create tasks for digging all the DNS_SERVERS
        and returns information with results."""
        record = record.upper()

        if record not in ALLOWED_RECORDS:
            record = DEFAULT_TYPE

        output = {
            'domain': self.domain,
            'record': record,
            'result': True,
            'data': {}
        }

        tasks = [asyncio.ensure_future(
            self._dig_task(server, record, output)) for server in ns_list]
        await asyncio.wait(tasks)

        return output

    async def dig_tg_message(self, record: str = DEFAULT_TYPE) -> str:
        """Generates telegram message with dig information about domain."""
        dig_output = await self.dig(record=record)
        domain = dig_output.pop('domain')
        record = dig_output.pop('record')

        message = [messages.DIG_TG_LABEL.format(domain)]
        for ns, results in dig_output['data'].items():
            message.append(messages.DIG_RECORD_AT_NS.format(record, ns))
            if results:
                current_results = [result.get('content') for result in results]
                message.extend(current_results)
            else:
                message.append(messages.DIG_EMPTY_RESPONSE)

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
