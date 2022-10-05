import os
import subprocess
import datetime
import re
import idna
import logging

from pathlib import Path
from logging.handlers import RotatingFileHandler
from telegram.ext import CommandHandler, Updater, MessageHandler, Filters

import whois

from dotenv import load_dotenv

import messages
from exceptions import BadDomain

load_dotenv()

TOKEN = os.getenv('TOKEN')
DNS_SERVERS = ("8.8.8.8 1.1.1.1 ns1.hostiman.ru "
               "ns2.hostiman.ru ns3.hostiman.com ns4.hostiman.com")
ALLOWRD_RECORDS = ('TXT', 'A', 'MX', 'CNAME', 'AAAA', 'SOA', 'DNAME',
                   'DS', 'NS', 'SRV', 'PTR', 'CAA', 'TLSA')

# Length of width between key and value in whois
LJ_VALUE = 20

updater = Updater(token=TOKEN)

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


def send_message(message, context, chat):
    """Send message to telegram."""
    context.bot.send_message(chat_id=chat.id,
                             text=message,
                             disable_web_page_preview=True,
                             parse_mode='HTML'
                             )


def who(domain_name):
    """Make whois query and formats the output."""
    domain = whois.query(domain_name)
    decoded_domain = idna.decode(domain_name)
    if domain:
        whois_information = '🔍 Here is whois information:'
        if decoded_domain != domain_name:
            whois_information += ('\nIDN: '.ljust(LJ_VALUE)
                                  + f'<code>{domain_name}</code>')
        whois_information += ('\nDomain: '.ljust(LJ_VALUE)
                              + decoded_domain)
        for dom in domain.name_servers:
            whois_information += '\nNserver: '.ljust(LJ_VALUE) + dom
        if domain.registrar:
            whois_information += ('\nRegistrar: '.ljust(LJ_VALUE)
                                  + domain.registrar)
        if domain.creation_date:
            whois_information += ('\nCreated: '.ljust(LJ_VALUE)
                                  + str(domain.creation_date))
        if domain.expiration_date:
            if datetime.datetime.utcnow() < domain.expiration_date:
                whois_information += ('\nExpires: '.ljust(LJ_VALUE)
                                      + str(domain.expiration_date)
                                      + ' - active!')
            else:
                whois_information += ('\nExpires: '.ljust(LJ_VALUE)
                                      + str(domain.expiration_date)
                                      + '<b> - EXPIRED! 🛑</b>')
        return whois_information
    else:
        return messages.domain_not_registred


def domain_fixer(raw_domain):
    """Brings domain to the form: example.com."""
    fixed_domain = raw_domain.lower()
    fixed_domain = re.search(r'[.\w-]+\.[\w-]{2,}', fixed_domain)
    if fixed_domain:
        fixed_domain = fixed_domain.group(0)
        fixed_domain = idna.encode(fixed_domain).decode()
        return fixed_domain
    else:
        raise BadDomain(messages.bad_domain)


def di(domain_name, record_type):
    """Make dig query and return result."""
    record_type = record_type.upper()
    outputlist = f'🔍 Here is DIG {idna.decode(domain_name)}:\n\n'
    if record_type not in ALLOWRD_RECORDS:
        record_type = 'A'
    for server in DNS_SERVERS.split():
        temp = subprocess.run(
            ['dig', '+short', domain_name, f'@{server}', record_type],
            stdout=subprocess.PIPE
        )
        temp_output = temp.stdout.decode('utf-8')
        if not temp_output:
            temp_output = '- empty -\n'
        outputlist += f'▫ {record_type} at {server}:\n'
        outputlist += str(temp_output) + '\n'
    return outputlist


def main(update, context):
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
            domain = domain_fixer(domain)
        except BadDomain as error:
            logger.debug(messages.error_log.format(
                info.chat.username,
                input_message,
                'Bad domain'))
            send_message(str(error), context, chat)
        except Exception as error:
            logger.error(messages.new_exception.format(
                info.chat.username,
                input_message,
                error), exc_info=True)
        else:
            try:
                whois_output = who(domain)
                send_message(whois_output, context, chat)
            except whois.exceptions.UnknownTld as error:
                logger.debug(messages.error_log.format(
                    info.chat.username,
                    input_message,
                    error))
                send_message(messages.unknown_tld, context, chat)
            except whois.exceptions.WhoisPrivateRegistry as error:
                logger.debug(messages.error_log.format(
                    info.chat.username,
                    input_message,
                    error))
                message = '❗ ' + str(error) + '. Trying to dig...'
                send_message(message, context, chat)
            except Exception as error:
                logger.error(messages.new_exception.format(
                    info.chat.username,
                    input_message,
                    error), exc_info=True)
            finally:
                dig_output = di(domain, record_type)
                send_message(dig_output, context, chat)
    else:
        send_message(messages.wrong_request, context, chat)


def command_help(update, context):
    """Send help information with telegram command handler."""
    chat = update.effective_chat
    info = update.message
    if info.text == '/start':
        logger.info(
            f'Someone starts bot: {info.chat.username}, '
            f'{info.chat.first_name} {info.chat.last_name}, {chat.id}')
    context.bot.send_message(chat_id=chat.id, text=messages.help_text)


def run_telegram_pooling():
    """Telegram create handlers and pooling."""
    logger.info('Start pooling')
    updater.dispatcher.add_handler(CommandHandler('start', command_help))
    updater.dispatcher.add_handler(CommandHandler('help', command_help))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, main))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    run_telegram_pooling()
