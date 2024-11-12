# settings.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, ContextTypes
from utils.keyboard_utils import build_settings_keyboard  # Import the helper function for building keyboards
import database  # Import database functions as needed
from datetime import datetime, timedelta

DAYS, GAME_CATEGORY = range(2)

async def choose_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Создаем кнопки с семью ближайшими днями, включая сегодня
    today = datetime.now()
    days_buttons = [
        [InlineKeyboardButton((today + timedelta(days=i)).strftime('%A %d-%m'), callback_data=f"day_{i}")]
        for i in range(7)
    ]
    reply_markup = InlineKeyboardMarkup(days_buttons)
    await update.callback_query.edit_message_text("Выберите день:", reply_markup=reply_markup)
    return GAME_CATEGORY

async def choose_game_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Кнопки категорий игр
    categories_buttons = [
        [InlineKeyboardButton("WH40k", callback_data="category_WH40k")],
        [InlineKeyboardButton("WHAOS", callback_data="category_WHAOS")],
        [InlineKeyboardButton("Историчка", callback_data="category_Historical")]
    ]
    reply_markup = InlineKeyboardMarkup(categories_buttons)
    await update.callback_query.edit_message_text("Выберите категорию игры:", reply_markup=reply_markup)
    return ConversationHandler.END  # Завершаем после выбора категории, но можем настроить дальнейшие действия

async def display_settings(update: Update, context: CallbackContext) -> int:
    """Displays the settings menu to the user."""
    user_id = update.effective_user.id

    # Retrieve settings options for the user, if any are specific to them
    settings_keyboard = build_settings_keyboard(user_id)
    markup = InlineKeyboardMarkup(settings_keyboard)

    # Send the settings menu to the user
    await update.callback_query.edit_message_text(
        text="Here are your settings options:",
        reply_markup=markup
    )
    return 0  # Return state for ConversationHandler if using one

async def update_setting_choice(update: Update, context: CallbackContext) -> None:
    """Updates a specific setting based on user choice."""
    query = update.callback_query
    data = query.data  # Data sent back from the button, e.g., 'set_notifications_on'

    # Example: parsing data to determine the action and execute it
    setting, action = data.split('_', 1)
    
    # Update the database or configuration based on the choice
    if setting == "notifications":
        if action == "on":
            await update_notifications(update, context, enable=True)
        elif action == "off":
            await update_notifications(update, context, enable=False)

    # Acknowledge the user's choice and update message text
    await query.answer()
    await query.edit_message_text(text=f"Setting '{setting}' updated to '{action}'.")

async def update_notifications(update: Update, context: CallbackContext, enable: bool) -> None:
    """Enables or disables notifications for the user."""
    user_id = update.effective_user.id

    # Update the database with the new setting value
    database.set_user_preference(user_id, "notifications", enable)

    # Send a confirmation message
    await context.bot.send_message(
        chat_id=user_id,
        text="Notifications have been " + ("enabled." if enable else "disabled.")
    )

