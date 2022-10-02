import os
import subprocess
import datetime
import re
import idna

from telegram.ext import CommandHandler, Updater, MessageHandler, Filters

import whois

from dotenv import load_dotenv

from exceptions import BadDomain

load_dotenv()

TOKEN = os.getenv('TOKEN')
DNS_SERVERS = ("8.8.8.8 1.1.1.1 ns1.hostiman.ru "
               "ns2.hostiman.ru ns3.hostiman.com ns4.hostiman.com")
ALLOWRD_RECORDS = ('TXT', 'A', 'MX', 'CNAME', 'AAAA', 'SOA', 'DNAME',
                   'DS', 'NS', 'SRV', 'PTR', 'CAA', 'TLSA')

updater = Updater(token=TOKEN)


def send_message(message, context, chat):
    """Send message to telegram."""
    context.bot.send_message(chat_id=chat.id,
                             text=message,
                             disable_web_page_preview=True)


def who(domain_name):
    """Make whois query and formate output."""
    domain = whois.query(domain_name)
    if domain:
        whois_information = '------- Here is whois information: -------\n'
        whois_information += ('%-15s%-15s' % ('Domain: ', domain.name) + '\n')
        for dom in domain.name_servers:
            whois_information += ('%-15s%-15s' % ('Nserver: ', dom) + '\n')
        if domain.registrar:
            whois_information += (
                    '%-15s%-15s' % ('Registrar: ', domain.registrar) + '\n')
        if domain.creation_date:
            whois_information += (
                    '%-15s%-15s' % ('Created: ', str(domain.creation_date))
                    + '\n')
        if domain.expiration_date:
            if datetime.datetime.utcnow() < domain.expiration_date:
                whois_information += (
                        '%-15s%-15s'
                        % ('Paid-till: ', str(domain.expiration_date)
                           + ' - active!') + '\n')
            else:
                whois_information += (
                        '%-15s%-15s'
                        % ('Paid-till: ', str(domain.expiration_date)
                           + ' - DOMAIN IS EXPIRED!') + '\n')
        return whois_information
    else:
        return 'Domain is not registred!'


def domain_fixer(raw_domain):
    """Brings domain to the form: example.com."""
    fixed_domain = raw_domain.lower()
    fixed_domain = re.search(r'[.\w\d-]*\.\w*', fixed_domain)
    if fixed_domain:
        fixed_domain = fixed_domain.group(0)
        fixed_domain = idna.encode(fixed_domain).decode()
        return fixed_domain
    else:
        raise BadDomain('Bad domain')


def di(domain_name, record_type):
    """Make dig query and return result."""
    outputlist = '------- Here is DIG information: -------\n'
    if record_type not in ALLOWRD_RECORDS:
        record_type = 'A'
    for server in DNS_SERVERS.split():
        temp = subprocess.run(
            ['dig', '+short', domain_name, f'@{server}', record_type],
            stdout=subprocess.PIPE
        )
        temp_output = temp.stdout.decode('utf-8')
        if not temp_output:
            temp_output = '- empty -'
        if record_type == 'TXT':
            outputlist += f'{record_type} at {server}:\n'
            outputlist += str(temp_output) + '\n'
        else:
            temp_output = temp.stdout.decode('utf-8').splitlines()
            temp_output = ' '.join(temp_output)
            outputlist += ('%-30s%-10s' % (f'{record_type} at {server}: ',
                                           str(temp_output) + '\n'))
    return outputlist


def main(update, context):
    """Main function for telegram message handler."""
    chat = update.effective_chat
    input_message = update.message.text.split()
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
            send_message(str(error), context, chat)
        else:
            try:
                whois_output = who(domain)
                send_message(whois_output, context, chat)
            except whois.exceptions.UnknownTld:
                send_message(
                    "I don't know this toplevel domain",
                    context,
                    chat
                )
            except whois.exceptions.WhoisPrivateRegistry as error:
                send_message(str(error), context, chat)
            finally:
                dig_output = di(domain, record_type)
                send_message(dig_output, context, chat)
    else:
        message = ('You send the wrong request. Please write '
                   '/help to get information about how to use the bot.')
        send_message(message, context, chat)


def command_help(update, context):
    """Send help information with telegram command handler."""
    chat = update.effective_chat
    help_text = (
        'Бот принимает команды вида: domain.ru MX, '
        'где вместо domain.ru - необходимо указать проверяемый домен, '
        'а вместо MX - тип проверяемой записи. Если не задать тип записи, '
        'или задать необслуживаемую запись, то '
        'бот будет по-умолчанию проверять А-запись.\nПримеры:\n\nПравильно:\n'
        'example.ru TXT\nhttp://example.com A\nsite.ru'
        '\n\nНеправильно:\nA site.com\nexample.ru A MX TXT')
    context.bot.send_message(chat_id=chat.id, text=help_text)


def run_telegram_pooling():
    """Telegram create handlers and pooling."""
    updater.dispatcher.add_handler(CommandHandler('start', command_help))
    updater.dispatcher.add_handler(CommandHandler('help', command_help))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, main))
    updater.start_polling()
    updater.idle()


run_telegram_pooling()
