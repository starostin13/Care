from datetime import datetime as dt
from telegram import InlineKeyboardButton

import sqllite_helper

async def get_keyboard_rules_keyboard_for_user(user_telegram: str):
    allready_scheduled_items =await sqllite_helper.get_schedule_by_user(user_telegram)
    
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
    items = [
        [InlineKeyboardButton("Settings", callback_data="callsettings")],
        [InlineKeyboardButton("Missions", callback_data="callmissions")]
    ]
    if await sqllite_helper.is_warmaster_registered(userId):
        items.append([InlineKeyboardButton("Games", callback_data="callgame")])
    
    return items

async def setting(userId):
    settings = await sqllite_helper.get_settings(userId)
    items = []
    
    if not settings:
        items.append([InlineKeyboardButton("Set the name", callback_data="requestsetname")])
    else:
        # Show current language
        current_language = settings[2] if settings[2] else 'en'
        items.append([InlineKeyboardButton(f"Language: {current_language}", callback_data="changelanguage")])
        
        # Show notification status
        notifications_on = settings[3] if len(settings) > 3 else 1
        notification_status = "ON" if notifications_on == 1 else "OFF"
        items.append([InlineKeyboardButton(f"Weekday notifications: {notification_status}", callback_data="togglenotifications")])
        
        if not settings[0]:  # nickname not set
            items.append([InlineKeyboardButton("Set the name", callback_data="requestsetname")])
        
        if not settings[1]:  # registered_as not set
            items.append([InlineKeyboardButton("Registration", callback_data="registration")])
    
    items.append([InlineKeyboardButton("Back", callback_data="start")])
    return items

async def missions_list(user_id):
    items = [[]]
    
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

async def today_schedule(user_id):
    today = dt.today()
    appointments = await sqllite_helper.get_schedule_with_warmasters(user_id, str(today.date()))
    buttons = [*map(lambda ap: InlineKeyboardButton(f'{ap[1]} {ap[2]}', callback_data=f'mission_sch_{ap[0]}'),appointments)]
    
    return [list(buttons)]


async def language_selection():
    languages = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru")],
        [InlineKeyboardButton("Back", callback_data="callsettings")]
    ]
    return languages