import os
import logging

import whois
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from telegram.ext import CommandHandler, Updater, MessageHandler, Filters

import messages
from exceptions import BadDomain
from wd import Domain

load_dotenv()
TOKEN = os.getenv('TOKEN')

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
