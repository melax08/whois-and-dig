import logging
import whois
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, MessageHandler,
                          filters, ContextTypes, CallbackQueryHandler)

import messages
from exceptions import BadDomain
from wd import Domain, DEFAULT_TYPE
from logger import configure_logging
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
        if update.message.text == '/start':
            logging.info(messages.SOMEONE_STARTS_BOT.format(
                chat.username, chat.first_name, chat.last_name, chat.id))
        await update.message.reply_html(messages.HELP_TEXT)

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
            await info.reply_html(messages.WRONG_REQUEST)
            return
        try:
            domain = Domain(domain)
        except BadDomain as error:
            logging.info(messages.ERROR_LOG.format(
                info.chat.username,
                input_message,
                messages.BAD_DOMAIN_LOG))
            await info.reply_text(str(error))
        except Exception as error:
            logging.error(messages.NEW_EXCEPTION.format(
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
                logging.info(messages.ERROR_LOG.format(
                    info.chat.username,
                    input_message,
                    error))
                await info.reply_html(messages.UNKNOWN_TLD,
                                      disable_web_page_preview=True)
            except (
                    whois.exceptions.WhoisPrivateRegistry,
                    whois.exceptions.FailedParsingWhoisOutput,
                    whois.exceptions.WhoisCommandFailed
            ) as error:
                logging.info(messages.ERROR_LOG.format(
                    info.chat.username,
                    input_message,
                    error))
                message = messages.WHOIS_ERROR.format(str(error).rstrip())
                await info.reply_html(message,
                                      disable_web_page_preview=True)
            except Exception as error:
                logging.error(messages.NEW_EXCEPTION.format(
                    info.chat.username,
                    input_message,
                    error), exc_info=True)
            finally:
                dig_output = await domain.dig_tg_message(record_type)
                reply_markup = None
                if len(domain.domain) <= MAX_DOMAIN_LEN_TO_BUTTONS:
                    reply_markup = InlineKeyboardMarkup.from_row(
                        self.create_dig_keyboard(str(domain)))
                await info.reply_html(
                    dig_output,
                    disable_web_page_preview=True,
                    reply_markup=reply_markup
                )

    def _collect_bot_handlers(self):
        """Adds bot handlers to telegram application instance."""
        self.application.add_handlers(
            (
                CommandHandler(['start', 'help'], self.command_help),
                MessageHandler(filters.TEXT, self.wd_main),
                CallbackQueryHandler(self.dig_buttons)
            )
        )

    def run_telegram_pooling(self) -> None:
        """Collects telegram handlers and starts pooling."""
        self._collect_bot_handlers()
        self.application.run_polling()


if __name__ == '__main__':
    configure_logging()
    application = Application.builder().token(TOKEN).build()
    wd_bot = WDTelegramBot(application)
    wd_bot.run_telegram_pooling()
