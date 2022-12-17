import logging
from enum import IntEnum, auto
from urllib.parse import urljoin

import requests

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
)

from tg_bot import bot_strings

logger = logging.getLogger(__name__)


class ConversationState(IntEnum):
    REQUESTED_PHONE = auto()
    SHOWED_NAME = auto()
    REQUESTED_NAME = auto()
    NEW_APPT = auto()
    ALL_OR_NEAREST = auto()
    SALON = auto()
    PROVIDER = auto()
    SERVICE = auto()
    DATETIME = auto()
    CONFIRM_APPT = auto()


BASE_URL = 'http://127.0.0.1:8000/'


new_appt_button = InlineKeyboardButton(bot_strings.new_appt, callback_data='new_appointment')
account_menu_button = InlineKeyboardButton(bot_strings.account_menu, callback_data='account')
main_menu_button = InlineKeyboardButton(bot_strings.main_menu, callback_data='back_to_main')
back_to_main_button = InlineKeyboardButton(bot_strings.back_to_main, callback_data='back_to_main')


def set_customer_id(update: Update, context: CallbackContext):
    url = urljoin(BASE_URL, 'customer')
    params = {'telegram_id': update.effective_user.id}
    try:
        response = requests.get(url, params)
        response.raise_for_status()
        return response.json()['data']['pk']

    except requests.HTTPError as exception:
        if exception.response.status_code == 404:
            message_text = bot_strings.not_registered_msg
            keyboard = [
                [InlineKeyboardButton(bot_strings.registration, callback_data='register')],
                [back_to_main_button],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.effective_chat.send_message(message_text, reply_markup=reply_markup)
        else:
            raise
    except (requests.HTTPError, requests.ConnectionError):
        return db_error(update, context)


def start(update, context):
    update.message.reply_text(
        text=bot_strings.welcome_msg)
    main_menu(update, context)


def main_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
        query.answer()
        query.message.delete()

    message_text = bot_strings.main_menu_msg

    keyboard = [
        [new_appt_button],
        [account_menu_button],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.effective_chat.send_message(message_text, reply_markup=reply_markup)


def db_error(update: Update, context: CallbackContext):
    update.effective_chat.send_message(bot_strings.db_error_message)
    return
