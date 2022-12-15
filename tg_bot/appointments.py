import json
import logging

import more_itertools
import requests
from more_itertools import chunked
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)

from tg_bot import base, bot_strings
from tg_bot.base import ConversationState

logger = logging.getLogger(__name__)


def update_request_query_params(query, context: CallbackContext):
    selection = query.data
    if 'choose_' in selection:
        return

    if 'provider' in selection:
        context.chat_data['provider_id'] = selection.replace('provider', '')
    if 'service' in selection:
        context.chat_data['service_id'] = selection.replace('service', '')
    if 'salon' in selection:
        context.chat_data['salon_id'] = selection.replace('salon', '')
    if 'lat' in selection:
        coordinates = json.loads(selection)
        context.chat_data.update(coordinates)

    print(f'{context.chat_data =}')


def clear_query_filters(context: CallbackContext):
    context.chat_data['provider_id'] = None
    context.chat_data['service_id'] = None
    context.chat_data['salon_id'] = None

    # TODO check needed?
    context.chat_data['lat'] = None
    context.chat_data['lon'] = None


def new_appointment(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    clear_query_filters(context)

    message_text = bot_strings.new_appointment_msg
    keyboard = [
        [InlineKeyboardButton(bot_strings.choose_salon, callback_data='choose_salon')],
        [InlineKeyboardButton(bot_strings.choose_service, callback_data='choose_service')],
        [InlineKeyboardButton(bot_strings.choose_provider, callback_data='choose_provider')],
        [base.back_to_main_button],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()


def choose_salon(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    update_request_query_params(query, context)
    url = f'http://127.0.0.1:8000/salons'
    params = context.chat_data
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except (requests.HTTPError, requests.ConnectionError):
        update.effective_chat.send_message(bot_strings.db_error_message)
        return base.main_menu(update, context)

    all_salons = response.json()['data']
    message_text = bot_strings.choose_salon_menu
    keyboard = []
    for salon in all_salons:
        keyboard.append([InlineKeyboardButton(salon['name'], callback_data=f'salon{salon["pk"]}')])
    keyboard.append(
        [base.back_to_new_appt_button])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()
    return ConversationState.SALON.value


def choose_provider(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    update_request_query_params(query, context)
    url = f'http://127.0.0.1:8000/providers'
    params = context.chat_data

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except (requests.HTTPError, requests.ConnectionError):
        update.effective_chat.send_message(bot_strings.db_error_message)
        return base.main_menu(update, context)

    providers = response.json()['data']
    message_text = bot_strings.choose_provider_menu
    keyboard = []
    for provider in providers:
        keyboard.append([InlineKeyboardButton(provider['first_name'], callback_data=f'provider{provider["pk"]}')])
    keyboard.append([base.back_to_new_appt_button])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()
    return ConversationState.PROVIDER.value


def choose_service(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    update_request_query_params(query, context)

    url = f'http://127.0.0.1:8000/services'
    params = context.chat_data
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except (requests.HTTPError, requests.ConnectionError):
        update.effective_chat.send_message(bot_strings.db_error_message)
        return base.main_menu(update, context)

    services = response.json()['data']
    message_text = bot_strings.choose_service_menu
    keyboard = []
    for service in services:
        keyboard.append([InlineKeyboardButton(service['name'], callback_data=f'service{service["pk"]}')])
    keyboard.append([base.back_to_new_appt_button])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()
    return ConversationState.SERVICE.value

# TODO handler
def choose_week(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    update_request_query_params(query, context)

    salon_id = context.chat_data['salon_id']
    url = f'http://127.0.0.1:8000/salon/{salon_id}/available_appointments/'
    params = context.chat_data['provider_id']

    try:
        response = requests.get(url, params)
    except (requests.HTTPError, requests.ConnectionError):
        update.effective_chat.send_message(bot_strings.db_error_message)
        return base.main_menu(update, context)

    appts = list(response.json()['data'].values)[0]
    appts_per_week = len(appts) // 4
    appts_by_week = list(more_itertools.chunked(appts, appts_per_week))
    context.chat_data['appts_by_week'] = appts_by_week

    keyboard = [
        [InlineKeyboardButton(bot_strings.this_week, callback_data='week0')],
        [InlineKeyboardButton(bot_strings.next_week, callback_data='week1')],
        [InlineKeyboardButton(bot_strings.week_after_2, callback_data='week2')],
        [InlineKeyboardButton(bot_strings.week_after_3, callback_data='week3')],
        [base.back_to_new_appt_button],
    ]
    query.edit_message_text(bot_strings.week_menu, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationState.WEEK.value

# TODO handler
def choose_date(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    selected_week = int(query.data.replace('week', ''))
    appts = context.chat_data['appts_by_week'][selected_week]
    keyboard = []
    for i, appt in enumerate(appts):
        button_label = f"{appt['date']}, {appt['weekday']}"
        keyboard.append(
            [InlineKeyboardButton(button_label, callback_data=f'date{i}')]
        )
    keyboard.append([InlineKeyboardButton(bot_strings.back_to_week, callback_data=selected_week)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(bot_strings.date_menu, reply_markup=reply_markup)
    query.message.delete()
    return ConversationState.DATE.value

# TODO choose hour


def confirm_appointment(update, context):
    query = update.callback_query
    query.answer()
    message_text = "Ваша запись:\n[дата]\n[услуга]\n[мастер]\n[салон]"
    keyboard = [
        [InlineKeyboardButton(bot_strings.confirm, callback_data='confirm')],
        [base.back_to_main_button],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()


def create_appointment(update, context):
    query = update.callback_query
    query.answer()
    update.effective_chat.send_message(bot_strings.appt_confirmed_msg)


coordinates_regex = r'^{"lat": \d*\.\d*, "lon": \d*\.\d*}$'

by_provider_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(choose_provider, pattern=r'^choose_provider$'),
    ],
    states={
        ConversationState.PROVIDER.value: [CallbackQueryHandler(choose_service, pattern=r'^provider\d$')],
        ConversationState.SERVICE.value: [CallbackQueryHandler(choose_salon, pattern=r'^service\d$')],
        ConversationState.SALON.value: [CallbackQueryHandler(choose_week, pattern=r'^salon\d$')],
        # CONFIRM: [CallbackQueryHandler(appointment_is_confirmed, pattern=r'^confirm$')]
    },
    fallbacks=[
        CallbackQueryHandler(choose_provider, pattern=r'^choose_provider$'),
        CommandHandler('start', base.start),
    ]
)

by_salon_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(choose_salon, pattern=r'^choose_salon$'),
    ],
    states={
        ConversationState.SALON.value: [CallbackQueryHandler(choose_service, pattern=r'^salon\d$')],
        ConversationState.SERVICE.value: [CallbackQueryHandler(choose_provider, pattern=r'^service\d$')],
        ConversationState.PROVIDER.value: [CallbackQueryHandler(choose_week, pattern=r'^provider\d$')]
    },
    fallbacks=[
        CallbackQueryHandler(choose_salon, pattern=r'^choose_salon$'),
        CommandHandler('start', base.start),
    ]
)

by_service_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(choose_service, pattern=r'^choose_service$'),
    ],
    states={
        ConversationState.SERVICE.value: [CallbackQueryHandler(choose_salon, pattern=r'^service\d$')],
        ConversationState.SALON.value: [CallbackQueryHandler(choose_provider, pattern=r'^salon\d$')],
        ConversationState.PROVIDER.value: [CallbackQueryHandler(choose_week, pattern=r'^provider\d$')]
    },
    fallbacks=[
        CallbackQueryHandler(choose_salon, pattern=r'^choose_service$'),
        CommandHandler('start', base.start),
    ]
)
