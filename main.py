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
        text=f'Привет! Добро пожаловать в бот BeautyCity!')
    menu(update, context)
    #registration(update, context)


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
        #'phone_number': get_users_phone(update, context)
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

    # TODO организовать очерёдность салон/услуга/мастер в зависимости от выбранного варианта
    if text == 'По салону':
        by_salon(update, context)

    if text == 'По  услуге':
        by_service(update, context)

    if text == 'По мастеру':
        by_master(update, context)

    if text == 'Политика обработки данных':
        send_file_policy(update, context)


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