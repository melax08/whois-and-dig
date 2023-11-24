from typing import Tuple
import logging

import whois
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, MessageHandler,
                          filters, ContextTypes, CallbackQueryHandler)
from telegram.error import BadRequest

import messages
from exceptions import BadDomain, BotWrongInput
from wd import Domain, DEFAULT_TYPE
from logger import configure_logging
from constants import TOKEN, MAX_DOMAIN_LEN_TO_BUTTONS, RECORDS_ON_KEYBOARD


class WDTelegramBot:
    MAX_INPUT_ARGUMENTS: int = 2

    def __init__(self, application) -> None:
        self.application = application

    @staticmethod
    def create_dig_keyboard(domain: str) -> list:
        """Create InlineKeyboard buttons for dig message."""
        keyboard = [
            InlineKeyboardButton(record, callback_data=f"{domain} {record}")
            for record in RECORDS_ON_KEYBOARD
        ]
        return keyboard

    async def dig_buttons(self, update, context) -> None:
        """Processing buttons under dig message."""
        query = update.callback_query
        domain, record = query.data.split()
        domain = Domain(domain)
        dig_output = await domain.dig_tg_message(record)
        await query.answer()
        try:
            await query.edit_message_text(
                text=dig_output,
                reply_markup=InlineKeyboardMarkup.from_row(
                    self.create_dig_keyboard(str(domain)))
            )
        except BadRequest:
            pass

    @staticmethod
    async def error_handler(
            update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Log the error and send a telegram message to notify the current user
        about the problem."""
        username = text = None

        if update is not None:
            username = update.effective_chat.username
            text = update.message.text

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=messages.INTERNAL_ERROR
            )

        logging.error(
            messages.NEW_EXCEPTION.format(username, text),
            exc_info=context.error
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

    def __get_domain_and_record(self, input_message: str) -> Tuple[str, str]:
        """
        Gets a domain and a record from the inputted message by user.
        - Examples of correct user inputs:
        example.com A
        example.com
        - Example of wrong user input:
        example.com A TXT MX
        """
        input_message = input_message.split()
        if not input_message or len(input_message) > self.MAX_INPUT_ARGUMENTS:
            raise BotWrongInput

        if len(input_message) != self.MAX_INPUT_ARGUMENTS:
            input_message.append(DEFAULT_TYPE)

        domain, record = input_message
        return domain, record

    @staticmethod
    async def __send_whois_information(update_message, domain: Domain) -> None:
        """Trying to make a whois query and sends the user message with
        result."""
        try:
            whois_output = domain.whois_tg_message()
            await update_message.reply_html(whois_output,
                                            disable_web_page_preview=True)
        except whois.exceptions.UnknownTld as error:
            logging.info(messages.ERROR_LOG.format(
                update_message.chat.username,
                update_message.text,
                error))
            await update_message.reply_html(messages.UNKNOWN_TLD,
                                            disable_web_page_preview=True)
        except (
                whois.exceptions.WhoisPrivateRegistry,
                whois.exceptions.FailedParsingWhoisOutput,
                whois.exceptions.WhoisCommandFailed
        ) as error:
            logging.info(messages.ERROR_LOG.format(
                update_message.chat.username,
                update_message.text,
                error))
            message = messages.WHOIS_ERROR.format(str(error).rstrip())
            await update_message.reply_html(message,
                                            disable_web_page_preview=True)

    async def __send_dig_information(
            self, update_message, domain: Domain, record: str
    ) -> None:
        """Trying to make a dig query and sends the user message with
        result."""
        dig_output = await domain.dig_tg_message(record)

        reply_markup = None
        if len(domain.domain) <= MAX_DOMAIN_LEN_TO_BUTTONS:
            reply_markup = InlineKeyboardMarkup.from_row(
                self.create_dig_keyboard(str(domain)))

        await update_message.reply_html(
            dig_output,
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )

    async def wd_main(
            self, update: Update, context: ContextTypes.context) -> None:
        """
        The main function for handle user message requests and return
        Whois & Dig information.
        If message not new (was edited the old message), makes only dig query.
        """
        info = update.message
        if update.edited_message:
            info = update.edited_message

        try:
            domain, record_type = self.__get_domain_and_record(info.text)
            domain = Domain(domain)
        except BotWrongInput:
            await info.reply_html(messages.WRONG_REQUEST)
        except BadDomain as error:
            logging.info(messages.ERROR_LOG.format(
                info.chat.username,
                info.text,
                messages.BAD_DOMAIN_LOG))
            await info.reply_text(str(error))
        else:
            if not update.edited_message:
                await self.__send_whois_information(info, domain)

            await self.__send_dig_information(info, domain, record_type)

    def _collect_bot_handlers(self):
        """Adds bot handlers to telegram application instance."""
        self.application.add_error_handler(self.error_handler)
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
