import os
from dotenv import load_dotenv
import logging
import django.db

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
        # [
        #     InlineKeyboardButton(bot_strings.favorite_recipes_button, callback_data='favorite_recipes'),
        # ],
        # [
        #     InlineKeyboardButton(bot_strings.excluded_recipes_button, callback_data='excluded_recipes'),
        # ],
        [
            InlineKeyboardButton(bot_strings.back_button, callback_data='back_to_main'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()


def my_appointments(update, context):
    update.message.reply_text(
        text="Мои записи:",
    )


def past_appointments(update, context):
    buttons = ['Запись 1', 'Запись 2', 'Назад']
    reply_markup = get_keyboard(buttons)
    update.message.reply_text(
        text="Прошлые записи:",
        reply_markup=reply_markup,
    )


def new_appointment(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

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


def by_salon_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    try:
        all_salons = [{'id': 1,
                       'name': 'Ближайший по геопозиции'},
                      {'id': 2,
                       'name': 'Салон 1'},
                      {'id': 3,
                       'name': 'Салон 2'}]
    except django.db.Error:
        update.effective_chat.send_message(bot_strings.db_error_message)
        return main_menu(update, context)

    message_text = bot_strings.by_salon_menu
    keyboard = []
    for salon in all_salons:
        keyboard.append([InlineKeyboardButton(salon.name, callback_data=f'show_by_salon_{salon.id}')])
    keyboard.append([InlineKeyboardButton(bot_strings.back_button, callback_data='back_to_main')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(message_text, reply_markup=reply_markup)
    query.message.delete()


def by_master(update, context):
    buttons = ['Мастер 1', 'Мастер 2', 'Назад']
    reply_markup = get_keyboard(buttons)
    update.message.reply_text(
        text="Выбор мастера",
        reply_markup=reply_markup,
    )


def by_service(update, context):
    buttons = ['Услуга 1', 'Услуга 2', 'Назад']
    reply_markup = get_keyboard(buttons)
    update.message.reply_text(
        text="Выбор услуги",
        reply_markup=reply_markup,
    )


def get_users_phone(update, context):
    reply_markup = ReplyKeyboardMarkup([[KeyboardButton(str('Предоставить номер телефона'), request_contact=True)]],
                                       resize_keyboard=True)
    message = 'Предоставьте свой номер телефона'
    context.bot.sendMessage(update.effective_chat.id, message, reply_markup=reply_markup)


# TODO сделать, чтобы новые кнопки не появлялись, пока пользователь не даст телефон
def registration(update, context):
    buttons = ['Политика обработки данных', 'Я даю согласие на обработку данных']
    reply_markup = get_keyboard(buttons)
    users_personal_data = {
        'first_name': update.message.from_user.first_name,
        'last_name': update.message.from_user.last_name,
        # 'phone_number': get_users_phone(update, context)
    }
    update.message.reply_text(
        text="Регистрация",
        reply_markup=reply_markup,
    )


def send_file_policy(update, context):
    context.bot.sendDocument(
        chat_id=update.message.chat_id,
        document=open('file.pdf', 'rb'),
        caption='Политика обработки данных'
    )


def confirm_appointment(update, context):
    buttons = ['Подтвердить запись', 'Назад']
    reply_markup = get_keyboard(buttons)
    update.message.reply_text(
        text="Ваша запись:\n[дата]\n[услуга]\n[мастер]\n[салон]",
        reply_markup=reply_markup,
    )


def help_message(update: Update, context: CallbackContext):
    """Send help text"""
    update.effective_chat.send_message('TEXT: HELP')


class Command(BaseCommand):
    help = 'Запуск чат-бота'

    def handle(self, *args, **options):
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

        dispatcher.add_handler(CallbackQueryHandler(account_menu, pattern=r'^account$'))
        dispatcher.add_handler(CallbackQueryHandler(new_appointment, pattern=r'^new_appointment$'))
        dispatcher.add_handler(CallbackQueryHandler(by_salon_menu, pattern=r'^by_salon$'))

        dispatcher.add_handler(CallbackQueryHandler(main_menu, pattern=r'^main_menu$|^back_to_main$'))

        dispatcher.add_handler(conversation_handler)

        updater.start_polling()
        updater.idle()


if __name__ == '__main__':
    Command().handle()
