# schedule.py

from datetime import datetime
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import players_helper
import sqllite_helper
import keyboard_constructor
import logging

# Initialize logger
logger = logging.getLogger(__name__)

SCHEDULE = 3

async def im_in(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Registers a user for a scheduled game and notifies them of their opponents."""
    query = update.callback_query
    data = query.data
    data_arr = data.split(',')
    # data_arr example: ['Sat Apr 27 00:00:00 2024', 'rule:killteam']

    try:
        # Insert schedule into the database
        sqllite_helper.insert_to_schedule(
            datetime.strptime(data_arr[0], '%c'),
            data_arr[1].split(':')[1],
            update.effective_user.id
        )
        
        # Retrieve opponents for the user and notify them
        opponents = await players_helper.get_opponents(update.effective_user.id, data)
        await query.edit_message_text("You will face the following opponents:")

        for opponent in opponents:
            if opponent[1] is not None:
                await update.effective_chat.send_contact(
                    first_name=str(opponent[0]), phone_number=opponent[1]
                )
    except Exception as e:
        logger.error(f"Error in scheduling or notifying opponents: {e}")
        await query.edit_message_text("An error occurred while scheduling your game. Please try again.")
    
    return SCHEDULE

async def show_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the user’s schedule with available game times."""
    menu = await keyboard_constructor.this_week(update.effective_user.id)
    markup = InlineKeyboardMarkup(menu)
    query = update.callback_query
    await query.edit_message_text("Available game times for the week:", reply_markup=markup)
    return SCHEDULE
