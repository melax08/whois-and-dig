import os
import subprocess
import datetime
import re
import logging
import json

import idna
import whois
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from telegram.ext import CommandHandler, Updater, MessageHandler, Filters

import messages
from exceptions import BadDomain


LJ_VALUE = 20


def domain_encode(domain):
    """Encode domain from IDN to punycode."""
    try:
        domain = idna.encode(domain)
    except idna.core.InvalidCodepoint:
        return domain
    return domain.decode()


def domain_decode(domain):
    """Decode domain from punycode to IDN."""
    try:
        domain = idna.decode(domain)
    except idna.core.InvalidCodepoint:
        return domain
    return domain


class Domain:
    def __init__(self, raw_site):
        self.raw_site = raw_site

    def domain_getter(self):
        domain = self.raw_site.lower()
        domain = re.search(r'[.\w-]+\.[\w-]{2,}', domain)
        if domain:
            domain = domain.group(0)
            domain = domain_encode(domain)
            return domain
        else:
            raise BadDomain(messages.bad_domain)

    def whois_tg_message(self):
        """Make whois query and formats the output."""
        domain = self.domain_getter()
        decoded_domain = domain_decode(domain)
        query = whois.query(domain)
        if query:
            whois_information = '🔍 Here is whois information:'
            if decoded_domain != domain:
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

    def whois_json(self):
        domain = self.domain_getter()
        decoded_domain = domain_decode(domain)
        query = whois.query(domain).__dict__
        if decoded_domain != domain:
            query['name_IDN'] = decoded_domain
        return json.dumps(query, default=str)


dom = Domain('привет.рф')
print(dom.whois_json())
