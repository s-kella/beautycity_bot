import logging
from urllib.parse import urljoin

import requests
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      Update)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
)

from tg_bot import appointments, base, bot_strings
from tg_bot.base import ConversationState

logger = logging.getLogger(__name__)


def start_registration(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_reply_markup()
    message_text = bot_strings.policy_msg
    keyboard = [
        [InlineKeyboardButton(bot_strings.policy_agree, callback_data='policy_agree')],
        [base.back_to_main_button],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)


def request_phone(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.message.edit_reply_markup()
    message_text = bot_strings.request_phone_msg
    reply_markup = ReplyKeyboardMarkup(
        [[KeyboardButton(bot_strings.share_contact, request_contact=True)],
         [KeyboardButton(bot_strings.decline_contact)]],
        resize_keyboard=True)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    return ConversationState.REQUESTED_PHONE.value


def process_phone_decline(update: Update, context: CallbackContext):
    update.effective_chat.send_message(bot_strings.declined_contact, reply_markup=ReplyKeyboardRemove())
    return appointments.new_appointment(update, context)


def show_name(update: Update, context: CallbackContext):
    context.chat_data['phone'] = update.message.contact.phone_number
    update.effective_chat.send_message(bot_strings.thanks, reply_markup=ReplyKeyboardRemove())

    full_name = update.effective_user.full_name
    message_text = bot_strings.confirm_name_msg.format(full_name)
    keyboard = [
        [InlineKeyboardButton(bot_strings.confirm, callback_data='confirm_name')],
        [InlineKeyboardButton(bot_strings.change, callback_data='change_name')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)

    return ConversationState.SHOWED_NAME.value


def complete_registration(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    url = urljoin(base.BASE_URL, 'register_customer/')
    customer = {
        'name': context.chat_data.get('customer_name') or update.effective_user.full_name,
        'telegram_id': update.effective_user.id,
        'phone_number': context.chat_data['phone'],
    }
    try:
        response = requests.post(url, data=customer)
        response.raise_for_status()
    except (requests.HTTPError, requests.ConnectionError):
        return base.db_error(update, context)

    message_text = bot_strings.registration_successful
    keyboard = [[base.main_menu_button]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(message_text, reply_markup=reply_markup)


def change_name(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.message.edit_reply_markup()
    update.effective_chat.send_message(bot_strings.request_name_msg)
    return ConversationState.REQUESTED_NAME.value


def reconfirm_name(update: Update, context: CallbackContext):
    full_name = update.message.text
    context.chat_data['customer_name'] = full_name
    message_text = bot_strings.confirm_name_msg.format(full_name)
    keyboard = [
        [InlineKeyboardButton(bot_strings.confirm, callback_data='confirm_name')],
        [InlineKeyboardButton(bot_strings.change, callback_data='change_name')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    return ConversationState.SHOWED_NAME.value


registration_conv = ConversationHandler(
    allow_reentry=True,
    entry_points=[
        CallbackQueryHandler(request_phone, pattern=r'^policy_agree$'),
    ],
    states={
        ConversationState.REQUESTED_PHONE.value: [
            MessageHandler(Filters.contact, show_name),
            MessageHandler(Filters.text, process_phone_decline)
        ],
        ConversationState.SHOWED_NAME.value: [
            CallbackQueryHandler(change_name, pattern=r'^change_name$'),
        ],
        ConversationState.REQUESTED_NAME.value: [MessageHandler(Filters.text, reconfirm_name)]
    },
    fallbacks=[
        CommandHandler('start', base.start),
        CallbackQueryHandler(complete_registration, pattern=r'^confirm_name$'),
    ]
)
