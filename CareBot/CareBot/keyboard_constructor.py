from telegram import InlineKeyboardButton
import numpy as np

import sqllite_helper

rulesNames = ["Kill Team", "Boarding Action", "WH40k", "Combat Patrol", "Battlefleet"]

async def get_keyboard_rules_keyboard_for_user(user_telegram: str):        
    buttons = list(map(lambda ruleName: InlineKeyboardButton(text=formatForButton(ruleName, user_telegram), callback_data=ruleName.replace(' ', '_').lover()), rulesNames))
        
    rules = np.reshape(buttons, int(len(buttons) ** 0.5))
    
    return rules
 
def formatForButton(text, user_telegram):
    allready_scheduled_items = sqllite_helper.get_schedule_by_user(user_telegram)
    if text in allready_scheduled_items:
        return '✅ ' + text
    else:
        return '➕ ' + text