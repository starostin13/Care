from datetime import datetime as dt
from telegram import InlineKeyboardButton

import sqllite_helper

async def get_keyboard_rules_keyboard_for_user(user_telegram: str):
    allready_scheduled_items = sqllite_helper.get_schedule_by_user(user_telegram)
    rulesNames = ["Kill Team", "Boarding Action", "WH40k", "Combat Patrol", "Battlefleet"]
    
    #for ruleName in rules:
    #    data = ruleName.relace(' ', '_').lower()
    
    rules = [[InlineKeyboardButton("Kill Team", callback_data="killteam"), InlineKeyboardButton("Boarding Action",callback_data="boardingaction")], [InlineKeyboardButton("WH40k 10",callback_data="wh40k"), InlineKeyboardButton("Combat patrol",callback_data="combatpatrol")], [InlineKeyboardButton("Battlefleet",callback_data="battlefleet")]]
    return rules
    
async def this_week():
    today = dt.today()
    week = today.isocalendar().week
    d = f"{today.year}-W{week}"
    menu_values = []
    for i in range(0, 7):
        menu_values.append(dt.strptime(f'{d}-{i}', "%Y-W%W-%w"))

    days = [
        [
            InlineKeyboardButton(menu_values[6].strftime("%A"), callback_data=menu_values[6].strftime("%c")),
            InlineKeyboardButton(menu_values[0].strftime("%A"), callback_data=menu_values[0].strftime("%c"))
        ],
        [
            InlineKeyboardButton(menu_values[5].strftime("%A"), callback_data=menu_values[5].strftime("%c")),
            InlineKeyboardButton(menu_values[4].strftime("%A"), callback_data=menu_values[4].strftime("%c")),
            InlineKeyboardButton(menu_values[3].strftime("%A"), callback_data=menu_values[3].strftime("%c")),
            InlineKeyboardButton(menu_values[2].strftime("%A"), callback_data=menu_values[2].strftime("%c")),
            InlineKeyboardButton(menu_values[1].strftime("%A"), callback_data=menu_values[1].strftime("%c"))
        ]
    ]
    
    return days