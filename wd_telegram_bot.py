import os
import logging

import whois
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from telegram import Update
from telegram.ext import (Application, CommandHandler, MessageHandler,
                          filters, ContextTypes)

import messages
from exceptions import BadDomain
from wd import Domain, DEFAULT_TYPE

load_dotenv()
TOKEN: str = os.getenv('TOKEN')

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

application = Application.builder().token(TOKEN).build()


class WDTelegramBot:
    def __init__(self, application) -> None:
        self.application = application

    @staticmethod
    async def command_help(update: Update, context: ContextTypes.context
                           ) -> None:
        """Send help information with telegram command handler."""
        chat = update.effective_chat
        info = update.message
        if info.text == '/start':
            logger.info(
                f'Someone starts bot: {info.chat.username}, '
                f'{info.chat.first_name} {info.chat.last_name}, {chat.id}')
        await info.reply_html(messages.help_text)

    @staticmethod
    async def wd_main(update: Update, context: ContextTypes.context) -> None:
        """Main function for handle user requests and return whois&dig info."""
        info = update.message
        edited_message = update.edited_message
        if edited_message:
            input_message = edited_message.text.split()
        else:
            input_message = info.text.split()
        domain = input_message[0]
        if len(input_message) == 2:
            record_type = input_message[1]
        elif len(input_message) == 1:
            record_type = DEFAULT_TYPE
        else:
            await info.reply_html(messages.wrong_request)
            return
        try:
            domain = Domain(domain)
        except BadDomain as error:
            logger.debug(messages.error_log.format(
                info.chat.username,
                input_message,
                'Bad domain'))
            await info.reply_text(str(error))
        except Exception as error:
            logger.error(messages.new_exception.format(
                info.chat.username,
                input_message,
                error), exc_info=True)
        else:
            try:
                if not edited_message:
                    whois_output = domain.whois_tg_message()
                    await info.reply_html(whois_output,
                                          disable_web_page_preview=True)
            except whois.exceptions.UnknownTld as error:
                logger.debug(messages.error_log.format(
                    info.chat.username,
                    input_message,
                    error))
                await info.reply_html(messages.unknown_tld,
                                      disable_web_page_preview=True)
            except (
                    whois.exceptions.WhoisPrivateRegistry,
                    whois.exceptions.FailedParsingWhoisOutput,
                    whois.exceptions.WhoisCommandFailed
            ) as error:
                logger.debug(messages.error_log.format(
                    info.chat.username,
                    input_message,
                    error))
                message = ('❗ Whois error: ' + str(error).rstrip()
                           + '. Trying to dig...')
                await info.reply_html(message,
                                      disable_web_page_preview=True)
            except Exception as error:
                logger.error(messages.new_exception.format(
                    info.chat.username,
                    input_message,
                    error), exc_info=True)
            finally:
                dig_output = domain.dig_tg_message(record_type)
                await info.reply_html(dig_output,
                                      disable_web_page_preview=True)

    def run_telegram_pooling(self) -> None:
        """Create telegram handlers and start pooling."""
        logger.info('Start pooling')
        self.application.add_handler(CommandHandler(
            ['start', 'help'], self.command_help))
        self.application.add_handler(MessageHandler(
            filters.TEXT, self.wd_main))
        application.run_polling()


if __name__ == '__main__':
    wd_bot = WDTelegramBot(application)
    wd_bot.run_telegram_pooling()
