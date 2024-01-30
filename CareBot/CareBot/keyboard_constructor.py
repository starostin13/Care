from telegram import InlineKeyboardButton

import sqllite_helper

async def get_keyboard_rules_keyboard_for_user(user_telegram: str):
    allready_scheduled_items = sqllite_helper.get_schedule_by_user(user_telegram)
    rulesNames = ["Kill Team", "Boarding Action", "WH40k", "Combat Patrol", "Battlefleet"]
    
    for ruleName in rules:
        data = ruleName.relace(' ', '_').lower()
    
    rules = [[InlineKeyboardButton("Kill Team", callback_data="killteam"), InlineKeyboardButton("Boarding Action",callback_data="boardingaction")], [InlineKeyboardButton("WH40k 10",callback_data="wh40k"), InlineKeyboardButton("Combat patrol",callback_data="combatpatrol")], [InlineKeyboardButton("Battlefleet",callback_data="battlefleet")]]
    return rules
    