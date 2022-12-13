import os
from dotenv import load_dotenv
import logging
import django.db
import requests

# from salons.models import Weekday, Salon, Provider, ProviderSchedule, Service, Customer, Appointment
from django.core.management.base import BaseCommand
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, LabeledPrice
from telegram import PreCheckoutQuery
from telegram import error as telegram_error
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    Updater,
    PreCheckoutQueryHandler,
)
import bot_strings

SALON, MASTER, SERVICE, DATE, CONFIRM = range(5)


def update_request_query_params(query, context: CallbackContext):
    selection = query.data
    if 'by_' in selection:
        return

    if 'master' in selection:
        context.chat_data['provider_id'] = selection.replace('master', '')
    if 'service' in selection:
        context.chat_data['service_id'] = selection.replace('service', '')
    if 'salon' in selection:
        context.chat_data['salon_id'] = selection.replace('salon', '')

    print(f'{context.chat_data =}')


def set_keyboards_buttons(buttons):
    keyboard = []
    for button in buttons:
        keyboard.append(KeyboardButton(button))
    return keyboard


def get_keyboard(buttons, one_time_keyboard=False):
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[set_keyboards_buttons(buttons)],
        resize_keyboard=True,
        one_time_keyboard=one_time_keyboard,
    )

    return reply_markup


def start(update, context):
    user = update.message.from_user
    update.message.reply_text(
        text=f'Привет! Добро пожаловать в бот BeautyCity!')
    main_menu(update, context)
    # registration(update, context)


def main_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
        query.answer()

    message_text = bot_strings.main_menu

    keyboard = [
        [
            InlineKeyboardButton(bot_strings.new_appointment_button, callback_data='new_appointment'),
        ],
        [
            InlineKeyboardButton(bot_strings.account_menu_button, callback_data='account'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.effective_chat.send_message(message_text, reply_markup=reply_markup)

    if query:
        query.message.delete()


def account_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    message_text = bot_strings.account_menu
    keyboard = [
        [
            InlineKeyboardButton(bot_strings.my_appointments, callback_data='my_ap'),
        ],
        [
            InlineKeyboardButton(bot_strings.past_appointments, callback_data='past_ap'),
        ],
        [
            InlineKeyboardButton(bot_strings.registration, callback_data='registration'),
        ],
        [
            InlineKeyboardButton(bot_strings.back_button, callback_data='back_to_main'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()


def my_appointments(update, context):
    query = update.callback_query
    query.answer()
    message_text = bot_strings.my_appointments
    keyboard = [
        [
            InlineKeyboardButton(bot_strings.back_button, callback_data='back_to_main'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()


def past_appointments(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    try:
        appointments = [{'id': 1,
                         'name': 'Запись 1'},
                        {'id': 2,
                         'name': 'Запись 2'}]
    except django.db.Error:
        update.effective_chat.send_message(bot_strings.db_error_message)
        return main_menu(update, context)

    message_text = bot_strings.past_appointments
    keyboard = [
        [
            InlineKeyboardButton(app['name'], callback_data=f'app{app["id"]}'),
        ] for app in appointments
    ]
    keyboard.append([
        InlineKeyboardButton(bot_strings.back_button, callback_data='back_to_main'),
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()


def new_appointment(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    context.chat_data.clear()

    message_text = bot_strings.new_appointment
    keyboard = [
        [
            InlineKeyboardButton(bot_strings.by_salon, callback_data='by_salon'),
        ],
        [
            InlineKeyboardButton(bot_strings.by_service, callback_data='by_service'),
        ],
        [
            InlineKeyboardButton(bot_strings.by_master, callback_data='by_master'),
        ],
        [
            InlineKeyboardButton(bot_strings.back_button, callback_data='back_to_main'),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()


def by_salon(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    update_request_query_params(query, context)
    url = f'http://127.0.0.1:8000/salons'
    params = context.chat_data

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

    except requests.HTTPError:
        update.effective_chat.send_message(bot_strings.db_error_message)
        return main_menu(update, context)

    all_salons = response.json()['data']
    message_text = bot_strings.by_salon_menu
    keyboard = [[InlineKeyboardButton(bot_strings.nearest_salon, callback_data='new_appointment')]]
    for salon in all_salons:

        keyboard.append([InlineKeyboardButton(salon['name'], callback_data=f'salon{salon["pk"]}')])
    keyboard.append(
        [InlineKeyboardButton(bot_strings.back_to_new_appointment_button, callback_data='new_appointment')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()
    return SALON


def by_master(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    update_request_query_params(query, context)
    url = f'http://127.0.0.1:8000/providers'
    params = context.chat_data

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

    except requests.HTTPError:
        update.effective_chat.send_message(bot_strings.db_error_message)
        return main_menu(update, context)

    masters = response.json()['data']
    message_text = bot_strings.by_master_menu
    keyboard = []
    for master in masters:
        keyboard.append([InlineKeyboardButton(master['first_name'], callback_data=f'master{master["pk"]}')])
    keyboard.append([InlineKeyboardButton(bot_strings.back_to_new_appointment_button, callback_data='new_appointment')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()
    return MASTER


def by_service(update: Update, context: CallbackContext):
    context.chat_data['service'] = 1
    query = update.callback_query
    query.answer()
    update_request_query_params(query, context)

    url = f'http://127.0.0.1:8000/services'
    params = context.chat_data

    try:

        response = requests.get(url, params=params)
        response.raise_for_status()

    except requests.HTTPError:
        update.effective_chat.send_message(bot_strings.db_error_message)
        return main_menu(update, context)

    services = response.json()['data']
    message_text = bot_strings.by_service_menu
    keyboard = []
    for service in services:
        keyboard.append([InlineKeyboardButton(service['name'], callback_data=f'service{service["pk"]}')])
    keyboard.append([InlineKeyboardButton(bot_strings.back_to_new_appointment_button, callback_data='new_appointment')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()
    return SERVICE


def by_date(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    salon_id = 1
    url = f'http://127.0.0.1:8000/salon/{salon_id}/available_appointments'
    response = requests.get(url)

    try:
        dates = response.json()['data']
    except requests.HTTPError:
        update.effective_chat.send_message(bot_strings.db_error_message)
        return main_menu(update, context)

    message_text = bot_strings.date_menu
    keyboard = []
    for date in dates:
        keyboard.append([InlineKeyboardButton(date['name'], callback_data=f'service{date["pk"]}')])
    keyboard.append([InlineKeyboardButton(bot_strings.back_to_new_appointment_button, callback_data='new_appointment')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()
    return DATE


def get_users_phone(update, context):
    query = update.callback_query
    query.answer()
    message_text = bot_strings.by_service_menu
    keyboard = [[
        InlineKeyboardButton(str('Предоставить номер телефона'), request_contact=True),
    ], [
        InlineKeyboardButton(bot_strings.back_button, callback_data='back_to_main'),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()

    # reply_markup = ReplyKeyboardMarkup([[KeyboardButton(str('Предоставить номер телефона'), request_contact=True)]],
    #                                    resize_keyboard=True)
    # message = 'Предоставьте свой номер телефона'
    # context.bot.sendMessage(update.effective_chat.id, message, reply_markup=reply_markup)


def registration(update, context):
    query = update.callback_query
    query.answer()
    message_text = bot_strings.registration
    keyboard = [[
        InlineKeyboardButton(bot_strings.policy, callback_data='policy'),
    ], [
        InlineKeyboardButton(bot_strings.policy_agree, callback_data='policy_agree')
    ], [
        InlineKeyboardButton(bot_strings.back_button, callback_data='back_to_main')
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()

    users_personal_data = {
        'first_name': update.message.from_user.first_name,
        'last_name': update.message.from_user.last_name
    }


def send_file_policy(update, context):
    query = update.callback_query
    query.answer()
    context.bot.sendDocument(
        chat_id=update.effective_chat.id,
        document=open('file.pdf', 'rb'),
        caption='Политика обработки данных'
    )


def appointment_is_confirmed(update, context):
    query = update.callback_query
    query.answer()
    context.bot.send_message(chat_id=update.effective_chat.id, text=bot_strings.confirmed)
    # message_text = bot_strings.confirmed
    # update.effective_chat.send_message(message_text)
    # query.message.delete()


def confirm_appointment(update, context):
    query = update.callback_query
    query.answer()
    message_text = "Ваша запись:\n[дата]\n[услуга]\n[мастер]\n[салон]"
    keyboard = [[
        InlineKeyboardButton(bot_strings.confirm, callback_data='confirm'),
    ], [
        InlineKeyboardButton(bot_strings.back_button, callback_data='back_to_main')
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()


def help_message(update: Update, context: CallbackContext):
    """Send help text"""
    update.effective_chat.send_message('TEXT: HELP')


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)

    load_dotenv()
    bot_token = os.getenv('TG_BOT_TOKEN')

    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher

    conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
        ],
        states={
        },
        fallbacks=[
            CommandHandler('start', start),
            MessageHandler(Filters.text, help_message),
        ]
    )

    conversation_handler_master = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(by_master, pattern=r'^by_master$'),
        ],
        states={
            MASTER: [CallbackQueryHandler(by_service, pattern=r'^master\d$')],
            SERVICE: [CallbackQueryHandler(by_salon, pattern=r'^service\d$')],
            SALON: [CallbackQueryHandler(confirm_appointment, pattern=r'^salon\d$')],
            # CONFIRM: [CallbackQueryHandler(appointment_is_confirmed, pattern=r'^confirm$')]
        },
        fallbacks=[
            CallbackQueryHandler(by_master, pattern=r'^by_master$')
        ]
    )

    conversation_handler_salon = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(by_salon, pattern=r'^by_salon$'),
        ],
        states={
            SALON: [CallbackQueryHandler(by_service, pattern=r'^salon\d$')],
            SERVICE: [CallbackQueryHandler(by_master, pattern=r'^service\d$')],
            MASTER: [CallbackQueryHandler(confirm_appointment, pattern=r'^master\d$')]
        },
        fallbacks=[
            CallbackQueryHandler(by_salon, pattern=r'^by_salon$')
        ]
    )

    conversation_handler_service = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(by_service, pattern=r'^by_service$'),
        ],
        states={
            SERVICE: [CallbackQueryHandler(by_salon, pattern=r'^service\d$')],
            SALON: [CallbackQueryHandler(by_master, pattern=r'^salon\d$')],
            MASTER: [CallbackQueryHandler(confirm_appointment, pattern=r'^master\d$')]
        },
        fallbacks=[
            CallbackQueryHandler(by_salon, pattern=r'^by_service$')
        ]
    )

    dispatcher.add_handler(CallbackQueryHandler(account_menu, pattern=r'^account$'))
    dispatcher.add_handler(CallbackQueryHandler(new_appointment, pattern=r'^new_appointment$'))
    dispatcher.add_handler(CallbackQueryHandler(past_appointments, pattern=r'^past_ap$'))
    dispatcher.add_handler(CallbackQueryHandler(my_appointments, pattern=r'^my_ap$'))

    dispatcher.add_handler(CallbackQueryHandler(main_menu, pattern=r'^main_menu$|^back_to_main$'))

    dispatcher.add_handler(conversation_handler)
    dispatcher.add_handler(conversation_handler_master)
    dispatcher.add_handler(conversation_handler_salon)
    dispatcher.add_handler(conversation_handler_service)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
