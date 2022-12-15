from telegram import InlineKeyboardButton

# Messages
welcome_msg = 'Привет! Добро пожаловать в бот BeautyCity!'
main_menu = ('Главное меню. Выберете новую запись или зайдите в личный кабинет, '
             'чтобы просмотреть ваши прошлые записи.')
account_menu_msg = 'Личный кабинет. Просмотрите...'
new_appointment_msg = 'Новая запись. Запишитесь...'
choose_salon = 'Выбор по салону'
choose_provider = 'Выбор по мастеру'
choose_service = 'Выбор по услуге'
db_error_message = 'При выполнении запроса произошла ошибка. Пожалуйста, повторите операцию позже.'

choose_salon_menu = 'Меню выбора по салону'
choose_provider_menu = 'Меню выбора по мастеру'
choose_service_menu = 'Меню выбора по услуге'
date_menu = 'Меню выбора даты'

phone_request = 'Предоставьте свой номер телефона'
nearest_salon = 'Ближайший салон'
policy = 'Политика обработки данных'
policy_agree = 'Я даю согласие на обработку данных'
confirm = 'Подтвердить запись'
confirmed = 'Ваша запись подтверждена'


# Button texts
new_appt = 'Новая запись'
back_to_new_appt = 'Обратно в новую запись'
account_menu = 'Личный кабинет'
back_to_main = 'Обратно в меню'
past_appointments = 'Прошлые записи'
my_appointments = 'Мои записи'
registration = 'Регистрация'

# Buttons
new_appt_button = InlineKeyboardButton(new_appt, callback_data='new_appointment')
back_to_new_appt_button = InlineKeyboardButton(back_to_new_appt, callback_data='new_appointment')
account_menu_button = InlineKeyboardButton(account_menu, callback_data='account')
back_to_main_button = InlineKeyboardButton(back_to_main, callback_data='back_to_main')
