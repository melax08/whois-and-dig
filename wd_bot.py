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

# Length of width between key and value
LJ_VALUE = 20

updater = Updater(token=TOKEN)


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
    if domain:
        whois_information = '🔍 Here is whois information:'
        whois_information += '\nDomain: '.ljust(LJ_VALUE) + idna.decode(domain.name)
        for dom in domain.name_servers:
            whois_information += '\nNserver: '.ljust(LJ_VALUE) + dom
        if domain.registrar:
            whois_information += '\nRegistrar: '.ljust(LJ_VALUE) + domain.registrar
        if domain.creation_date:
            whois_information += '\nCreated: '.ljust(LJ_VALUE) + str(domain.creation_date)
        if domain.expiration_date:
            if datetime.datetime.utcnow() < domain.expiration_date:
                whois_information += '\nExpires: '.ljust(LJ_VALUE) + str(domain.expiration_date) + ' - active!'
            else:
                whois_information += '\nExpires: '.ljust(LJ_VALUE) + str(domain.expiration_date) + '<b> - EXPIRED! 🛑</b>'
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
        raise BadDomain('❗ Bad domain. Maybe you need some /help?')


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
                    "❗ I don't know this second-level domain, but let's try some DIG 🌚",
                    context,
                    chat
                )
            except whois.exceptions.WhoisPrivateRegistry as error:
                message = '❗ ' + str(error) + '. Trying to dig...'
                send_message(message, context, chat)
            finally:
                dig_output = di(domain, record_type)
                send_message(dig_output, context, chat)
    else:
        message = ('❗ You send the wrong request. Maybe you need some /help?')
        send_message(message, context, chat)


def command_help(update, context):
    """Send help information with telegram command handler."""
    chat = update.effective_chat
    help_text = ('You can send messages like: example.com MX\n'
                 'Instead of example.com you need to specify domain name, that you want to check.\n'
                 'Instead of MX you need to specify the record type (A, TXT, MX, etc)\n'
                 'if you you will not specify the record type, or specify the wrong record name, the record type will set to "A".\n\n'
                 'Examples:\n\n'
                 '✅ Correct:\n'
                 'example.ru TXT\nhttp://example.com A\nsite.ru\n\n'
                 '❌ Wrong:\n'
                 'A site.com\nexample.ru A MX TXT')
    context.bot.send_message(chat_id=chat.id, text=help_text)


def run_telegram_pooling():
    """Telegram create handlers and pooling."""
    updater.dispatcher.add_handler(CommandHandler('start', command_help))
    updater.dispatcher.add_handler(CommandHandler('help', command_help))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, main))
    updater.start_polling()
    updater.idle()


def test_message():
    """Test function, don't use it in production."""
    from telegram import Bot
    bot = Bot(token=TOKEN)
    chat_id = '159956275'
    # text = di('google.com', 'MX')
    text = who('google.com')
    print(text)
    bot.send_message(chat_id,
                     text,
                     disable_web_page_preview=True,
                     parse_mode='HTML')


if __name__ == '__main__':
    run_telegram_pooling()
