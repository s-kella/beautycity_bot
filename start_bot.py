import logging
import os
from dotenv import load_dotenv

from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Updater,
)

from tg_bot import account, base, appointments, registration

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    load_dotenv()
    bot_token = os.getenv('TG_BOT_TOKEN')

    updater = Updater(token=bot_token, use_context=True)
    updater.bot.arbitrary_callback_data = True

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', base.start))

    dispatcher.add_handler(appointments.by_provider_conv)
    dispatcher.add_handler(appointments.by_salon_conv)
    dispatcher.add_handler(appointments.by_service_conv)
    dispatcher.add_handler(CallbackQueryHandler(appointments.new_appointment, pattern=r'^new_appointment$'))
    dispatcher.add_handler(CallbackQueryHandler(base.main_menu, pattern=r'^main_menu$|^back_to_main$'))

    dispatcher.add_handler(CallbackQueryHandler(account.account_menu, pattern=r'^account$'))
    dispatcher.add_handler(CallbackQueryHandler(account.past_appointments, pattern=r'^past_appts$'))
    dispatcher.add_handler(CallbackQueryHandler(account.future_appointments, pattern=r'^future_appts$'))

    dispatcher.add_handler(registration.registration_conv)
    dispatcher.add_handler(CallbackQueryHandler(registration.start_registration, pattern=r'^register$'))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
