from datetime import datetime as dt
from telegram import InlineKeyboardButton
import numpy as np

import sqllite_helper

async def get_keyboard_rules_keyboard_for_user(user_telegram: str):
    allready_scheduled_items = sqllite_helper.get_schedule_by_user(user_telegram)
    
    #for ruleName in rules:
    #    data = ruleName.relace(' ', '_').lower()
    
    rules = [
        [InlineKeyboardButton("Kill Team", callback_data="rule:killteam")],
        [InlineKeyboardButton("Boarding Action",callback_data="rule:boardingaction")],
        [InlineKeyboardButton("WH40k 10",callback_data="rule:wh40k")],
        [InlineKeyboardButton("Combat patrol",callback_data="rule:combatpatrol")],
        [InlineKeyboardButton("Battlefleet",callback_data="rule:battlefleet")],
    ]
    return rules

async def get_main_menu(userId):
    if sqllite_helper.is_warmaster_registered(userId)
    items = [
        [InlineKeyboardButton("Settings")]    
    ]
    
async def this_week(rule):
    today = dt.today()
    week = today.isocalendar().week
    d = f"{today.year}-W{week}"
    menu_values = []
    for i in range(0, 7):
        menu_values.append(dt.strptime(f'{d}-{i}', "%Y-W%W-%w"))

    days = [
        [
            InlineKeyboardButton(menu_values[6].strftime("%A"), callback_data=menu_values[6].strftime("%c") + ',' + rule),
            InlineKeyboardButton(menu_values[0].strftime("%A"), callback_data=menu_values[0].strftime("%c") + ',' + rule)
        ],
        [
            InlineKeyboardButton(menu_values[5].strftime("%A"), callback_data=menu_values[5].strftime("%c") + ',' + rule),
            InlineKeyboardButton(menu_values[4].strftime("%A"), callback_data=menu_values[4].strftime("%c") + ',' + rule),
            InlineKeyboardButton(menu_values[3].strftime("%A"), callback_data=menu_values[3].strftime("%c") + ',' + rule),
            InlineKeyboardButton(menu_values[2].strftime("%A"), callback_data=menu_values[2].strftime("%c") + ',' + rule),
            InlineKeyboardButton(menu_values[1].strftime("%A"), callback_data=menu_values[1].strftime("%c") + ',' + rule)
        ]
    ]
    
    return days