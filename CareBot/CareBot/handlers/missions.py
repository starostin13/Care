# missions.py

from telegram import Update
from telegram.ext import ContextTypes
import mission_helper
import sqllite_helper
import logging

# Initialize logger
logger = logging.getLogger(__name__)

MISSIONS = 4

async def get_the_mission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Fetches a mission from the database and notifies participants."""
    mission = await mission_helper.get_mission()
    query = update.callback_query
    data = query.data  # Data from the pressed button

    # Convert mission data to a formatted string
    mission_text = '\n'.join(
        f'#{mission[i]}' if i == 4 else str(item or '')
        for i, item in enumerate(mission)
    )

    # Send the mission text to the user
    await query.edit_message_text(
        f"{mission_text}\nTo record your game result, reply to this message with the score in the format [your points] [opponent's points], e.g., 20 0"
    )

    # Notify all participants of the event
    participants = await sqllite_helper.get_event_participants(data.rsplit('_', 1)[-1])

    for participant_id in participants:
        if participant_id != update.effective_user.id:
            try:
                await context.bot.send_message(chat_id=participant_id, text=f"New mission:\n{mission_text}")
            except Exception as e:
                logger.error(f"Error sending message to participant {participant_id}: {e}")

    return MISSIONS

async def handle_mission_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user replies to mission messages, logging the game result."""
    original_message = update.message.reply_to_message.text
    user_reply = update.message.text

    logger.info(f"User {update.effective_user.id} replied to '{original_message}' with '{user_reply}'")

    # Extract battle ID from the mission text
    battle_id = next((line for line in original_message.splitlines() if line.startswith('#')), None)

    if battle_id:
        await mission_helper.write_battle_result(battle_id, user_reply)
        await update.message.reply_text(f"Result received: {user_reply}. It has been recorded.")
    else:
        await update.message.reply_text("Error: Could not find mission ID. Please try again.")

async def show_missions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays a list of current missions for the user."""
    menu = await keyboard_constructor.today_schedule(update.effective_user.id)
    markup = InlineKeyboardMarkup(menu)
    query = update.callback_query
    await query.edit_message_text("Your current missions:", reply_markup=markup)
    return MISSIONS
