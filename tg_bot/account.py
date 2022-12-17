import logging
from urllib.parse import urljoin

import requests

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from tg_bot import base, bot_strings
from tg_bot.base import BASE_URL

logger = logging.getLogger(__name__)


def format_appointments_text(appointments, past: bool = False):
    if not appointments:
        return bot_strings.no_appointments
    message_text = bot_strings.past_appointments_msg if past else bot_strings.future_appointments_msg
    for appointment in appointments:
        message_text += (f"\n\n{appointment['datetime'].replace('T', ' ')}: {appointment['service']} "
                         f"у мастера {appointment['provider']} в салоне {appointment['salon']}.")
    return message_text


def account_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if 'customer_id' not in context.chat_data or context.chat_data['customer_id'] is None:
        customer_id = context.chat_data['customer_id'] = base.set_customer_id(update, context)
        if customer_id is None:
            return

    message_text = bot_strings.account_menu_msg
    keyboard = [
        [InlineKeyboardButton(bot_strings.future_appointments_label, callback_data='future_appts')],
        [InlineKeyboardButton(bot_strings.past_appointments_label, callback_data='past_appts')],
        [base.back_to_main_button],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(message_text, reply_markup=reply_markup)


def future_appointments(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    customer_id = context.chat_data['customer_id']
    url = urljoin(BASE_URL, f'/customer/{customer_id}/future')
    try:
        response = requests.get(url)
        response.raise_for_status()
    except (requests.HTTPError, requests.ConnectionError):
        return base.db_error(update, context)

    message_text = format_appointments_text(response.json()['data'])

    keyboard = [
        [base.back_to_main_button],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(message_text, reply_markup=reply_markup)


def past_appointments(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    customer_id = context.chat_data['customer_id']
    url = urljoin(BASE_URL, f'/customer/{customer_id}/past')
    try:
        response = requests.get(url)
        response.raise_for_status()
    except (requests.HTTPError, requests.ConnectionError):
        return base.db_error(update, context)

    message_text = format_appointments_text(response.json()['data'], past=True)
    keyboard = [
        [base.back_to_main_button],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(message_text, reply_markup=reply_markup)
