import os
from dotenv import load_dotenv
import logging
import requests

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
import bot_constants

# Conversation states
SALON, MASTER, SERVICE, DATE, CONFIRM = range(5)


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

    print(f'{context.chat_data =}')


def clear_query_filters(context: CallbackContext):
    context.chat_data['provider_id'] = None
    context.chat_data['service_id'] = None
    context.chat_data['salon_id'] = None

    # TODO check needed?
    context.chat_data['lat'] = None
    context.chat_data['lon'] = None


def start(update, context):
    update.message.reply_text(
        text=bot_constants.welcome_msg)
    main_menu(update, context)


def main_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
        query.answer()

    message_text = bot_constants.main_menu

    keyboard = [
        [bot_constants.new_appt_button],
        [bot_constants.account_menu_button],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.effective_chat.send_message(message_text, reply_markup=reply_markup)

    if query:
        query.message.delete()


def account_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if 'customer_id' not in context.chat_data:
        url = f'http://127.0.0.1:8000/customer'
        params = {'telegram_id': update.effective_user.id}
        try:
            response = requests.get(url, params)
        except requests.HTTPError:
            update.effective_chat.send_message(bot_constants.db_error_message)
            return main_menu(update, context)
        if response.status_code == 404:
            ...
            # TODO registration branch
        context.chat_data['customer_id'] = response.json()['data']['pk']


    message_text = bot_constants.account_menu_msg
    keyboard = [
        [InlineKeyboardButton(bot_constants.my_appointments, callback_data='my_appts')],
        [InlineKeyboardButton(bot_constants.past_appointments, callback_data='past_appts')],
        [InlineKeyboardButton(bot_constants.registration, callback_data='registration')],
        [bot_constants.back_to_main_button],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()


def my_appointments(update, context):
    query = update.callback_query
    query.answer()
    message_text = bot_constants.my_appointments
    keyboard = [
        [bot_constants.back_to_main_button],
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
    except requests.HTTPError:
        update.effective_chat.send_message(bot_constants.db_error_message)
        return main_menu(update, context)

    message_text = bot_constants.past_appointments
    keyboard = [
        [InlineKeyboardButton(app['name'], callback_data=f'app{app["id"]}')] for app in appointments
    ]
    keyboard.append([
        bot_constants.back_to_main_button,
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()


def new_appointment(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    clear_query_filters(context)

    message_text = bot_constants.new_appointment_msg
    keyboard = [
        [InlineKeyboardButton(bot_constants.choose_salon, callback_data='choose_salon')],
        [InlineKeyboardButton(bot_constants.choose_service, callback_data='choose_service')],
        [InlineKeyboardButton(bot_constants.choose_provider, callback_data='choose_provider')],
        [bot_constants.back_to_main_button],
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
    except requests.HTTPError:
        update.effective_chat.send_message(bot_constants.db_error_message)
        return main_menu(update, context)

    all_salons = response.json()['data']
    message_text = bot_constants.choose_salon_menu
    keyboard = []
    for salon in all_salons:
        keyboard.append([InlineKeyboardButton(salon['name'], callback_data=f'salon{salon["pk"]}')])
    keyboard.append(
        [bot_constants.back_to_new_appt_button])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()
    return SALON


def choose_provider(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    update_request_query_params(query, context)
    url = f'http://127.0.0.1:8000/providers'
    params = context.chat_data

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except requests.HTTPError:
        update.effective_chat.send_message(bot_constants.db_error_message)
        return main_menu(update, context)

    providers = response.json()['data']
    message_text = bot_constants.choose_provider_menu
    keyboard = []
    for provider in providers:
        keyboard.append([InlineKeyboardButton(provider['first_name'], callback_data=f'provider{provider["pk"]}')])
    keyboard.append([bot_constants.back_to_new_appt_button])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()
    return MASTER


def choose_service(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    update_request_query_params(query, context)

    url = f'http://127.0.0.1:8000/services'
    params = context.chat_data
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except requests.HTTPError:
        update.effective_chat.send_message(bot_constants.db_error_message)
        return main_menu(update, context)

    services = response.json()['data']
    message_text = bot_constants.choose_service_menu
    keyboard = []
    for service in services:
        keyboard.append([InlineKeyboardButton(service['name'], callback_data=f'service{service["pk"]}')])
    keyboard.append([bot_constants.back_to_new_appt_button])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()
    return SERVICE


def choose_date(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    salon_id = 1
    url = f'http://127.0.0.1:8000/salon/{salon_id}/available_appointments'
    response = requests.get(url)

    # FIXME
    try:
        dates = response.json()['data']
    except requests.HTTPError:
        update.effective_chat.send_message(bot_constants.db_error_message)
        return main_menu(update, context)

    message_text = bot_constants.date_menu
    keyboard = []
    for date in dates:
        keyboard.append([InlineKeyboardButton(date['name'], callback_data=f'service{date["pk"]}')])
    keyboard.append([bot_constants.back_to_new_appt_button])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()
    return DATE


def get_users_phone(update, context):
    query = update.callback_query
    query.answer()
    message_text = bot_constants.choose_service_menu
    keyboard = [
        [InlineKeyboardButton('Предоставить номер телефона', request_contact=True)],
        [bot_constants.back_to_main_button],
    ]
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
    message_text = bot_constants.registration
    keyboard = [
        [InlineKeyboardButton(bot_constants.policy, callback_data='policy')],
        [InlineKeyboardButton(bot_constants.policy_agree, callback_data='policy_agree')],
        [bot_constants.back_to_main_button],
    ]
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
    context.bot.send_message(chat_id=update.effective_chat.id, text=bot_constants.confirmed)
    # message_text = bot_constants.confirmed
    # update.effective_chat.send_message(message_text)
    # query.message.delete()


def confirm_appointment(update, context):
    query = update.callback_query
    query.answer()
    message_text = "Ваша запись:\n[дата]\n[услуга]\n[мастер]\n[салон]"
    keyboard = [
        [InlineKeyboardButton(bot_constants.confirm, callback_data='confirm')], 
        [bot_constants.back_to_main_button],
    ]
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

    conversation_handler_provider = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(choose_provider, pattern=r'^choose_provider$'),
        ],
        states={
            MASTER: [CallbackQueryHandler(choose_service, pattern=r'^provider\d$')],
            SERVICE: [CallbackQueryHandler(choose_salon, pattern=r'^service\d$')],
            SALON: [CallbackQueryHandler(confirm_appointment, pattern=r'^salon\d$')],
            # CONFIRM: [CallbackQueryHandler(appointment_is_confirmed, pattern=r'^confirm$')]
        },
        fallbacks=[
            CallbackQueryHandler(choose_provider, pattern=r'^choose_provider$')
        ]
    )

    conversation_handler_salon = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(choose_salon, pattern=r'^choose_salon$'),
        ],
        states={
            SALON: [CallbackQueryHandler(choose_service, pattern=r'^salon\d$')],
            SERVICE: [CallbackQueryHandler(choose_provider, pattern=r'^service\d$')],
            MASTER: [CallbackQueryHandler(confirm_appointment, pattern=r'^provider\d$')]
        },
        fallbacks=[
            CallbackQueryHandler(choose_salon, pattern=r'^choose_salon$')
        ]
    )

    conversation_handler_service = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(choose_service, pattern=r'^choose_service$'),
        ],
        states={
            SERVICE: [CallbackQueryHandler(choose_salon, pattern=r'^service\d$')],
            SALON: [CallbackQueryHandler(choose_provider, pattern=r'^salon\d$')],
            MASTER: [CallbackQueryHandler(confirm_appointment, pattern=r'^provider\d$')]
        },
        fallbacks=[
            CallbackQueryHandler(choose_salon, pattern=r'^choose_service$')
        ]
    )

    dispatcher.add_handler(CallbackQueryHandler(account_menu, pattern=r'^account$'))
    dispatcher.add_handler(CallbackQueryHandler(new_appointment, pattern=r'^new_appointment$'))
    dispatcher.add_handler(CallbackQueryHandler(past_appointments, pattern=r'^past_appts$'))
    dispatcher.add_handler(CallbackQueryHandler(my_appointments, pattern=r'^my_appts$'))

    dispatcher.add_handler(CallbackQueryHandler(main_menu, pattern=r'^main_menu$|^back_to_main$'))

    dispatcher.add_handler(conversation_handler)
    dispatcher.add_handler(conversation_handler_provider)
    dispatcher.add_handler(conversation_handler_salon)
    dispatcher.add_handler(conversation_handler_service)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
