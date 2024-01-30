from telegram import InlineKeyboardButton
import numpy as np

import sqllite_helper

rulesNames = ["Kill Team", "Boarding Action", "WH40k", "Combat Patrol", "Battlefleet"]

async def get_keyboard_rules_keyboard_for_user(user_telegram: str):
    allready_scheduled_items = sqllite_helper.get_schedule_by_user(user_telegram)
        
    buttons = list(map(lambda ruleName: InlineKeyboardButton(text=ruleName, callback_data=ruleName.replace(' ', '_').lover()), rulesNames))
    
    rules = np.reshape(buttons, int(len(buttons) ** 0.5))
    
    return rules
    