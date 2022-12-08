import os
from dotenv import load_dotenv

from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove


def set_keyboards_buttons(buttons):
    keyboard = []
    for button in buttons:
        keyboard.append(KeyboardButton(button))
    return keyboard


def get_keyboard(buttons, one_time_keyboard=False):
    reply_markup = ReplyKeyboardMarkup (
            keyboard = [set_keyboards_buttons(buttons)],
            resize_keyboard = True,
            one_time_keyboard = one_time_keyboard,
        )

    return reply_markup


def start(update, context):
    user = update.message.from_user
    update.message.reply_text(
        text=f'Привет! Добро пожаловать бот BeautyCity!')
    menu(update, context)


def menu(update, context):
    buttons = ['Личный кабинет', 'Записаться']
    reply_markup = get_keyboard(buttons)
    update.message.reply_text(
        text="Главное меню:",
        reply_markup=reply_markup,
    )


def lk(update, context):
    buttons = ['Мои записи', 'Прошлые записи', 'Назад']
    reply_markup = get_keyboard(buttons)
    update.message.reply_text(
        text="Личный кабинет:",
        reply_markup=reply_markup,
    )


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


def new_appointment(update, context):
    buttons = ['По салону', 'По  услуге', 'По мастеру', 'Назад']
    reply_markup = get_keyboard(buttons)
    update.message.reply_text(
        text="Новая запись",
        reply_markup=reply_markup,
    )


def by_salon(update, context):
    buttons = ['Ближайший по геолокации', 'Салон 1', 'Салон 2', 'Назад']
    reply_markup = get_keyboard(buttons)
    update.message.reply_text(
        text="Выбор салона",
        reply_markup=reply_markup,
    )


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


def message_handler(update, context):
    text = update.message.text

    if text == 'Назад':
        menu(update, context)

    if text == 'Личный кабинет':
        lk(update, context)

    if text == 'Мои записи':
        my_appointments(update, context)

    if text == 'Прошлые записи':
        past_appointments(update, context)

    if text == 'Записаться':
        new_appointment(update, context)

    if text == 'По салону':
        by_salon(update, context)

    if text == 'По  услуге':
        by_service(update, context)

    if text == 'По мастеру':
        by_master(update, context)


if __name__ == '__main__':
    load_dotenv()
    bot_token = os.getenv('TG_BOT_TOKEN')

    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    updater.dispatcher.add_handler(MessageHandler(Filters.all, message_handler))

    updater.start_polling()
    updater.idle()