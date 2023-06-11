import whois
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, MessageHandler,
                          filters, ContextTypes, CallbackQueryHandler)

import messages
from exceptions import BadDomain
from wd import Domain, DEFAULT_TYPE
from configs import configure_tg_bot_logging
from constants import TOKEN, MAX_DOMAIN_LEN_TO_BUTTONS


class WDTelegramBot:
    def __init__(self, application) -> None:
        self.application = application

    @staticmethod
    def create_dig_keyboard(domain: str) -> list:
        """Create InlineKeyboard buttons for dig message."""
        keyboard = [
            InlineKeyboardButton("A", callback_data=f"{domain} A"),
            InlineKeyboardButton("AAAA", callback_data=f"{domain} AAAA"),
            InlineKeyboardButton("CNAME", callback_data=f"{domain} CNAME"),
            InlineKeyboardButton("TXT", callback_data=f"{domain} TXT"),
            InlineKeyboardButton("MX", callback_data=f"{domain} MX"),
            InlineKeyboardButton("SOA", callback_data=f"{domain} SOA"),
        ]
        return keyboard

    async def dig_buttons(self, update, context) -> None:
        """Processing buttons under dig message."""
        query = update.callback_query
        domain, record = query.data.split()
        domain = Domain(domain)
        dig_output = domain.dig_tg_message(record)
        await query.edit_message_text(
            text=dig_output,
            reply_markup=InlineKeyboardMarkup.from_row(
                self.create_dig_keyboard(str(domain)))
        )

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

    async def wd_main(
            self, update: Update, context: ContextTypes.context) -> None:
        """Main function for handle user requests and return whois&dig info."""
        info = update.message
        if update.edited_message:
            info = update.edited_message
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
                if not update.edited_message:
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
                reply_markup = None
                if len(domain.domain) <= MAX_DOMAIN_LEN_TO_BUTTONS:
                    reply_markup = InlineKeyboardMarkup.from_row(
                        self.create_dig_keyboard(str(domain)))
                await info.reply_html(
                    dig_output,
                    disable_web_page_preview=True,
                    reply_markup=reply_markup
                )

    def run_telegram_pooling(self) -> None:
        """Create telegram handlers and start pooling."""
        logger.info('Start pooling')
        self.application.add_handler(CommandHandler(
            ['start', 'help'], self.command_help))
        self.application.add_handler(MessageHandler(
            filters.TEXT, self.wd_main))
        self.application.add_handler(CallbackQueryHandler(self.dig_buttons))
        application.run_polling()


if __name__ == '__main__':
    logger = configure_tg_bot_logging()
    application = Application.builder().token(TOKEN).build()
    wd_bot = WDTelegramBot(application)
    wd_bot.run_telegram_pooling()
