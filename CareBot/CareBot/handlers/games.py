from telegram import InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes
import logging
import sqllite_helper
import players_helper

logger = logging.getLogger(__name__)

async def appoint(update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userId = update.effective_user.id
    query = update.callback_query
    rules = await keyboard_constructor.get_keyboard_rules_keyboard_for_user(userId)
    menu = InlineKeyboardMarkup(rules)
    await query.edit_message_text(f'Choose the rules {update.effective_user.first_name}', reply_markup=menu)
    return GAMES

async def im_in(update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    data = query.data
    data_arr = data.split(',')
    sqllite_helper.insert_to_schedule(
        datetime.strptime(data_arr[0], '%c'),
        data_arr[1].split(':')[1],
        update.effective_user.id
    )
    opponents = await players_helper.get_opponents(update.effective_user.id, data)
    await query.edit_message_text(f'You will face off with')
    for opponent in opponents:
        if opponent[1] is not None:
            await update.effective_chat.send_contact(first_name=str(opponent[0]), phone_number=opponent[1])
