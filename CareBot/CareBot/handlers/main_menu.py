# main_menu.py

from telegram import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes
import keyboard_constructor
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Main menu and state definition
MAIN_MENU = 0

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    # Ensure the user is registered or initialized in the system
    await context.bot.send_message(chat_id=user_id, text="Welcome to the Crusade Bot!")
    
    menu = await keyboard_constructor.get_main_menu()
    reply_markup = ReplyKeyboardMarkup(menu, resize_keyboard=True)
    await update.message.reply_text("Hi! Choose an option:", reply_markup=reply_markup)
    
    return MAIN_MENU

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Greet new users when they send a message to the bot."""
    await update.message.reply_text(
        "Welcome to the Crusade Bot! Please type /start to begin."
    )
