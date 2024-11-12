#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8

from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

import config
import logging
from handlers import games, registration, missions, settings, main_menu
from handlers.registration import set_name
from handlers.settings import choose_day, choose_game_category

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Определение всех состояний
MAIN_MENU, SETTINGS, GAMES, SCHEDULE, MISSIONS, DAYS, GAME_CATEGORY = range(7)

# Initialize bot application with the token
bot = ApplicationBuilder().token(config.crusade_care_bot_telegram_token).build()

# Main conversation handler with states
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", main_menu.hello)],
    states={
        MAIN_MENU: [
            CallbackQueryHandler(registration.set_name, pattern='^requestsetname$'),
            CallbackQueryHandler(settings.display_settings, pattern='^callsettings$'),
            CallbackQueryHandler(games.appoint, pattern="^callgame$"),
            CallbackQueryHandler(registration.contact_callback, pattern='^registration$'),
            CallbackQueryHandler(missions.show_missions, pattern='^callmissions$')
        ],
        SETTINGS: [
            CallbackQueryHandler(games.im_in)
        ],
        GAMES: [            
            CallbackQueryHandler(choose_day, pattern='^callgames$')  # Начинаем с выбора дня
        ],
        DAYS: [
            CallbackQueryHandler(choose_game_category, pattern="^day_\\d+$")  # Переходим к выбору категории
        ],
        GAME_CATEGORY: [
            CallbackQueryHandler(games.im_in)  # Далее можно обработать выбор категории или завершить
        ],
        SCHEDULE: [
            CallbackQueryHandler(games.im_in)
        ],
        MISSIONS: [
            CallbackQueryHandler(missions.get_the_mission)    
        ]
    },
    fallbacks=[CommandHandler("start", main_menu.hello)],
)

# Register additional handlers
bot.add_handler(MessageHandler(filters.REPLY & filters.TEXT, missions.handle_mission_reply))
bot.add_handler(conv_handler)
bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu.welcome))
bot.add_handler(CommandHandler("setname", set_name))
bot.add_handler(CommandHandler("regme", registration.contact))
bot.add_handler(MessageHandler(filters.CONTACT, registration.contact_callback))


# Run the bot
bot.run_polling()
