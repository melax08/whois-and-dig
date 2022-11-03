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

load_dotenv()

TOKEN = os.getenv('TOKEN')

LJ_VALUE = 20
ALLOWED_RECORDS = ('TXT', 'A', 'MX', 'CNAME', 'AAAA', 'SOA', 'DNAME',
                   'DS', 'NS', 'SRV', 'PTR', 'CAA', 'TLSA')
DNS_SERVERS = ("8.8.8.8 1.1.1.1 ns1.hostiman.ru "
               "ns2.hostiman.ru ns3.hostiman.com ns4.hostiman.com")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
log_file = 'wd_bot.log'
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_file)
handler = RotatingFileHandler(log_path, maxBytes=50000000, backupCount=5)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

updater = Updater(token=TOKEN)

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
        self.domain = self.domain_getter()

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

    def whois_json(self):
        decoded_domain = domain_decode(self.domain)
        query = whois.query(self.domain)
        if query:
            if decoded_domain != self.domain:
                query.__dict__['name_IDN'] = decoded_domain
            return json.dumps(query.__dict__, default=str, ensure_ascii=False)
        return json.dumps({'message': 'Domain is not registred'})

    def dig_tg_message(self, record='A'):
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

    def dig_json(self, record='A'):
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


class WDTelegramBot:
    def __init__(self, updater):
        self.updater = updater

    def send_message(self, message, context, chat):
        """Send message to telegram."""
        context.bot.send_message(chat_id=chat.id,
                                 text=message,
                                 disable_web_page_preview=True,
                                 parse_mode='HTML'
                                 )

    def command_help(self, update, context):
        """Send help information with telegram command handler."""
        chat = update.effective_chat
        info = update.message
        if info.text == '/start':
            logger.info(
                f'Someone starts bot: {info.chat.username}, '
                f'{info.chat.first_name} {info.chat.last_name}, {chat.id}')
        context.bot.send_message(chat_id=chat.id, text=messages.help_text)

    def wd_main(self, update, context):
        """Main function for telegram message handler."""
        chat = update.effective_chat
        info = update.message
        input_message = info.text.split()
        domain = ''
        record_type = ''
        if len(input_message) == 2:
            domain = input_message[0]
            record_type = input_message[1]
        elif len(input_message) == 1:
            domain = input_message[0]
            record_type = 'A'
        if len(input_message) == 1 or len(input_message) == 2:
            try:
                domain = Domain(domain)
            except BadDomain as error:
                logger.debug(messages.error_log.format(
                    info.chat.username,
                    input_message,
                    'Bad domain'))
                self.send_message(str(error), context, chat)
            except Exception as error:
                logger.error(messages.new_exception.format(
                    info.chat.username,
                    input_message,
                    error), exc_info=True)
            else:
                try:
                    whois_output = domain.whois_tg_message()
                    self.send_message(whois_output, context, chat)
                except whois.exceptions.UnknownTld as error:
                    logger.debug(messages.error_log.format(
                        info.chat.username,
                        input_message,
                        error))
                    self.send_message(messages.unknown_tld, context, chat)
                except (whois.exceptions.WhoisPrivateRegistry,
                        whois.exceptions.FailedParsingWhoisOutput) as error:
                    logger.debug(messages.error_log.format(
                        info.chat.username,
                        input_message,
                        error))
                    message = '❗ ' + str(error) + '. Trying to dig...'
                    self.send_message(message, context, chat)
                except Exception as error:
                    logger.error(messages.new_exception.format(
                        info.chat.username,
                        input_message,
                        error), exc_info=True)
                finally:
                    dig_output = domain.dig_tg_message(record_type)
                    self.send_message(dig_output, context, chat)
                    del domain
        else:
            self.send_message(messages.wrong_request, context, chat)

    def run_telegram_pooling(self):
        """Telegram create handlers and pooling."""
        logger.info('Start pooling')
        self.updater.dispatcher.add_handler(
            CommandHandler(['start', 'help'], self.command_help))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text,
                                                           self.wd_main))
        self.updater.start_polling()
        self.updater.idle()


if __name__ == '__main__':
    wd_bot = WDTelegramBot(updater)
    wd_bot.run_telegram_pooling()
