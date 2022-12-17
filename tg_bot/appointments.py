import json
import logging
from urllib.parse import urljoin

import more_itertools
import requests
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      Update)
from telegram.ext import (CallbackContext, CallbackQueryHandler, 
                          ConversationHandler, CommandHandler,
                          Filters, MessageHandler)

from tg_bot import base, bot_strings
from tg_bot.base import BASE_URL, ConversationState

logger = logging.getLogger(__name__)

back_to_week_button = InlineKeyboardButton(bot_strings.back_to_week, callback_data='choose_week')
back_to_new_appt_button = InlineKeyboardButton(bot_strings.back_to_new_appt, callback_data='new_appointment')


def update_request_query_params(query, context: CallbackContext):
    selection = query.data
    if 'choose_' in selection or 'all_' in selection:
        return
    context.chat_data.update(json.loads(selection))


def clear_appointment_filters(context: CallbackContext):
    customer_id = context.chat_data.get('customer_id')
    context.chat_data.clear()
    context.chat_data['customer_id'] = customer_id


def new_appointment(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
        query.answer()
        query.message.delete()

    clear_appointment_filters(context)

    message_text = bot_strings.new_appointment_msg
    keyboard = [
        [InlineKeyboardButton(bot_strings.choose_salon, callback_data='choose_salon')],
        [InlineKeyboardButton(bot_strings.choose_service, callback_data='choose_service')],
        [InlineKeyboardButton(bot_strings.choose_provider, callback_data='choose_provider')],
        [base.back_to_main_button],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    return ConversationHandler.END


def salon_all_or_nearest(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    update_request_query_params(query, context)
    keyboard = [
        [InlineKeyboardButton(bot_strings.all_salons, callback_data='all_salons')],
        [InlineKeyboardButton(bot_strings.nearest_salons, callback_data='nearest_salons')],
    ]
    query.edit_message_text(bot_strings.salon_all_or_nearest, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationState.ALL_OR_NEAREST.value


def request_location(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    keyboard = [
        [KeyboardButton(bot_strings.send_location, request_location=True)],
        [KeyboardButton(bot_strings.decline_location)]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.effective_chat.send_message(bot_strings.request_location, reply_markup=reply_markup)
    query.message.delete()
    return ConversationState.ALL_OR_NEAREST.value


def process_location(update: Update, context: CallbackContext):
    location = update.message.location
    context.chat_data['lat'] = location.latitude
    context.chat_data['lon'] = location.longitude
    update.effective_chat.send_message(bot_strings.thanks, reply_markup=ReplyKeyboardRemove())
    return choose_salon(update, context)


def process_refused_location(update: Update, context: CallbackContext):
    update.effective_chat.send_message(bot_strings.ok, reply_markup=ReplyKeyboardRemove())
    return choose_salon(update, context)


def choose_salon(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
        query.answer()
        update_request_query_params(query, context)

    url = urljoin(BASE_URL, 'salons/')
    params = {k: v for k, v in context.chat_data.items() if k in ['service_id', 'provider_id', 'lat', 'lon']}
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
        salon_info = f"{salon['name']}, {salon['address']}"
        if 'distance' in salon:
            salon_display = f"{salon['name']}, {salon['distance']} км"
        else:
            salon_display = salon_info
        callback_data = {'salon_id': salon['pk'],
                         'salon_info': salon_info}
        keyboard.append([
            InlineKeyboardButton(salon_display,
                                 callback_data=json.dumps(callback_data))
        ])
    keyboard.extend([[back_to_new_appt_button], [base.back_to_main_button]])

    reply_markup = InlineKeyboardMarkup(keyboard)
    if query:
        query.edit_message_text(message_text, reply_markup=reply_markup)
    else:
        update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    return ConversationState.SALON.value


def choose_provider(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    update_request_query_params(query, context)
    url = urljoin(BASE_URL, 'providers/')
    params = {k: v for k, v in context.chat_data.items() if k in ['service_id', 'salon_id']}

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
        provider_full_name = f"{provider['first_name']} {provider['last_name']}"
        callback_data = {'provider_id': provider['pk'],
                         'provider_name': provider_full_name}
        keyboard.append([
            InlineKeyboardButton(provider_full_name,
                                 callback_data=json.dumps(callback_data))
        ])
    keyboard.extend([[back_to_new_appt_button], [base.back_to_main_button]])
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(message_text, reply_markup=reply_markup)
    return ConversationState.PROVIDER.value


def choose_service(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    update_request_query_params(query, context)

    url = urljoin(BASE_URL, 'services/')
    params = {k: v for k, v in context.chat_data.items() if k in ['provider_id', 'salon_id']}
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
        callback_data = {'service_id': service['pk'],
                         'service_name': service['name']}
        keyboard.append([
            InlineKeyboardButton(service['name'],
                                 callback_data=json.dumps(callback_data))
        ])
    keyboard.extend([[back_to_new_appt_button], [base.back_to_main_button]])
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(message_text, reply_markup=reply_markup)
    return ConversationState.SERVICE.value


def choose_week(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    update_request_query_params(query, context)

    salon_id = context.chat_data['salon_id']
    url = urljoin(BASE_URL, f'salon/{salon_id}/available_appointments/')
    params = {'provider_id': context.chat_data['provider_id']}

    try:
        response = requests.get(url, params)
        response.raise_for_status()
    except (requests.HTTPError, requests.ConnectionError):
        update.effective_chat.send_message(bot_strings.db_error_message)
        return base.main_menu(update, context)

    appts = list(response.json()['data'].values())[0]
    appts_per_week = len(appts) // 4
    appts_by_week = list(more_itertools.chunked(appts, appts_per_week))
    context.chat_data['appts_by_week'] = appts_by_week

    keyboard = [
        [InlineKeyboardButton(bot_strings.this_week, callback_data='week0')],
        [InlineKeyboardButton(bot_strings.next_week, callback_data='week1')],
        [InlineKeyboardButton(bot_strings.week_after_2, callback_data='week2')],
        [InlineKeyboardButton(bot_strings.week_after_3, callback_data='week3')],
        [back_to_new_appt_button], [base.back_to_main_button]
    ]
    query.edit_message_text(bot_strings.week_menu, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationState.DATETIME.value


def choose_date(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    selected_week = int(query.data.replace('week', ''))
    appts = context.chat_data['appts_by_week'][selected_week]
    keyboard = []
    for appt in appts:
        button_label = f"{appt['date']}, {appt['weekday']}"
        keyboard.append(
            [InlineKeyboardButton(button_label, callback_data=f"{appt['date']},week{selected_week}")]
        )
    keyboard.extend([
        [InlineKeyboardButton(bot_strings.back_to_week, callback_data='choose_week')],
        [back_to_new_appt_button], [base.back_to_main_button]
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(bot_strings.date_menu, reply_markup=reply_markup)
    return ConversationState.DATETIME.value


def choose_hour(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    selected_date, selected_week = query.data.split(',week')
    appts = context.chat_data['appts_by_week'][int(selected_week)]
    appts_for_date = next(appt for appt in appts if appt['date'] == selected_date)
    keyboard = [[]]
    for hour in appts_for_date['available_hours']:
        keyboard[-1].append(InlineKeyboardButton(f'{hour}:00', callback_data=f'{selected_date},hour{hour}'))
        if len(keyboard[-1]) > 4:
            keyboard.append([])
    keyboard.extend([[InlineKeyboardButton(bot_strings.back_to_date, callback_data=f'week{selected_week}')],
                     [back_to_new_appt_button], [base.back_to_main_button]])
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(bot_strings.hour_menu, reply_markup=reply_markup)
    return ConversationState.DATETIME.value


def confirm_appointment(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    selected_date, selected_hour = query.data.split(',hour')
    context.chat_data.update({'date': selected_date,
                              'hour': selected_hour})
    selected_service = context.chat_data['service_name']
    selected_provider = context.chat_data['provider_name']
    selected_salon = context.chat_data['salon_info']

    query.edit_message_text(f"Вы выбрали запись:")

    appt_text = (f"{selected_date} {selected_hour}:00\n"
                 f"{selected_service} "
                 f"у мастера {selected_provider} "
                 f"в салоне {selected_salon}.")

    keyboard = [
        [InlineKeyboardButton(bot_strings.confirm, callback_data='confirm_appt')],
        [InlineKeyboardButton(bot_strings.back_to_date, callback_data='choose_week')],
        [back_to_new_appt_button],
        [base.back_to_main_button],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    appt_message = update.effective_chat.send_message(appt_text, reply_markup=reply_markup)
    context.chat_data['appt_message_id'] = appt_message.message_id


def create_appointment(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if 'customer_id' not in context.chat_data or context.chat_data['customer_id'] is None:
        customer_id = context.chat_data['customer_id'] = base.set_customer_id(update, context)
        if customer_id is None:
            return

    appt = {k: v for k, v in context.chat_data.items() if k in ['hour', 'date', 'customer_id',
                                                                'provider_id', 'service_id']}
    url = urljoin(BASE_URL, 'make_appointment/')
    try:
        response = requests.post(url, data=appt)
        response.raise_for_status()
    except (requests.HTTPError, requests.ConnectionError):
        update.effective_chat.send_message(bot_strings.db_error_message)
        return base.main_menu(update, context)

    query.edit_message_reply_markup()
    keyboard = [[InlineKeyboardButton(bot_strings.main_menu, callback_data='back_to_main')]]

    update.effective_chat.send_message(bot_strings.appt_confirmed_msg, reply_markup=InlineKeyboardMarkup(keyboard))
    update.effective_chat.pin_message(context.chat_data['appt_message_id'])


coordinates_regex = r'^{"lat": \d*\.\d*, "lon": \d*\.\d*}$'
provider_regex = r'^{"provider_id": .*"}$'
salon_regex = r'^{"salon_id": .*"}$'
service_regex = r'^{"service_id": .*"}$'

by_provider_conv = ConversationHandler(
    allow_reentry=True,
    entry_points=[
        CallbackQueryHandler(choose_provider, pattern=r'^choose_provider$'),
    ],
    states={
        ConversationState.PROVIDER.value: [CallbackQueryHandler(choose_service, pattern=provider_regex)],
        ConversationState.SERVICE.value: [CallbackQueryHandler(salon_all_or_nearest, pattern=service_regex)],
        ConversationState.ALL_OR_NEAREST.value: [
            CallbackQueryHandler(request_location, pattern='nearest_salons'),
            CallbackQueryHandler(choose_salon, pattern='all_salons'),
            MessageHandler(Filters.location, process_location),
            MessageHandler(Filters.text, process_refused_location),
        ],
        ConversationState.SALON.value: [CallbackQueryHandler(choose_week, pattern=salon_regex)],
        ConversationState.DATETIME.value: [
            CallbackQueryHandler(choose_date, pattern=r'^week\d$'),
            CallbackQueryHandler(choose_week, pattern=r'^choose_week$'),
            CallbackQueryHandler(choose_hour, pattern=r'^\d{4}-\d{2}-\d{2},week\d$'),
            CallbackQueryHandler(confirm_appointment, pattern=r'^\d{4}-\d{2}-\d{2},hour\d\d?$')
        ],
    },
    fallbacks=[
        CallbackQueryHandler(new_appointment, pattern=r'^new_appointment'),
        CallbackQueryHandler(base.main_menu, pattern='^back_to_main$'),
        CallbackQueryHandler(create_appointment, pattern='^confirm_appt$'),
        CommandHandler('start', base.start),
    ]
)

by_salon_conv = ConversationHandler(
    allow_reentry=True,
    entry_points=[
        CallbackQueryHandler(salon_all_or_nearest, pattern=r'^choose_salon$'),
    ],
    states={
        ConversationState.ALL_OR_NEAREST.value: [
                    CallbackQueryHandler(request_location, pattern='nearest_salons'),
                    CallbackQueryHandler(choose_salon, pattern='all_salons'),
                    MessageHandler(Filters.location, process_location),
                    MessageHandler(Filters.text, process_refused_location),
        ],
        ConversationState.SALON.value: [CallbackQueryHandler(choose_service, pattern=salon_regex)],
        ConversationState.SERVICE.value: [CallbackQueryHandler(choose_provider, pattern=service_regex)],
        ConversationState.PROVIDER.value: [CallbackQueryHandler(choose_week, pattern=provider_regex)],
        ConversationState.DATETIME.value: [
            CallbackQueryHandler(choose_date, pattern=r'^week\d$'),
            CallbackQueryHandler(choose_week, pattern=r'^choose_week$'),
            CallbackQueryHandler(choose_hour, pattern=r'^\d{4}-\d{2}-\d{2},week\d$'),
            CallbackQueryHandler(confirm_appointment, pattern=r'^\d{4}-\d{2}-\d{2},hour\d\d?$')
        ],
    },
    fallbacks=[
        CallbackQueryHandler(new_appointment, pattern=r'^new_appointment'),
        CallbackQueryHandler(base.main_menu, pattern='^back_to_main$'),
        CallbackQueryHandler(create_appointment, pattern='^confirm_appt$'),
        CommandHandler('start', base.start),
    ]
)

by_service_conv = ConversationHandler(
    allow_reentry=True,
    entry_points=[
        CallbackQueryHandler(choose_service, pattern=r'^choose_service$'),
    ],
    states={
        ConversationState.SERVICE.value: [CallbackQueryHandler(salon_all_or_nearest, pattern=service_regex)],
        ConversationState.ALL_OR_NEAREST.value: [
                    CallbackQueryHandler(request_location, pattern='nearest_salons'),
                    CallbackQueryHandler(choose_salon, pattern='all_salons'),
                    MessageHandler(Filters.location, process_location),
                    MessageHandler(Filters.text, process_refused_location),
        ],
        ConversationState.SALON.value: [CallbackQueryHandler(choose_provider, pattern=salon_regex)],
        ConversationState.PROVIDER.value: [CallbackQueryHandler(choose_week, pattern=provider_regex)],
        ConversationState.DATETIME.value: [
            CallbackQueryHandler(choose_date, pattern=r'^week\d$'),
            CallbackQueryHandler(choose_week, pattern=r'^choose_week$'),
            CallbackQueryHandler(choose_hour, pattern=r'^\d{4}-\d{2}-\d{2},week\d$'),
            CallbackQueryHandler(confirm_appointment, pattern=r'^\d{4}-\d{2}-\d{2},hour\d\d?$')
        ],
    },
    fallbacks=[
        CallbackQueryHandler(new_appointment, pattern=r'^new_appointment'),
        CallbackQueryHandler(base.main_menu, pattern='^back_to_main$'),
        CallbackQueryHandler(create_appointment, pattern='^confirm_appt$'),
        CommandHandler('start', base.start),
    ]
)
