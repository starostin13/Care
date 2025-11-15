from datetime import datetime as dt
from telegram import InlineKeyboardButton

import settings_helper
import schedule_helper
import localization
import sqllite_helper

async def get_keyboard_rules_keyboard_for_user(user_telegram: str):
    allready_scheduled_items = await schedule_helper.get_user_scheduled_games(user_telegram)
    
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
    items = []
    
    # Check if user has a nickname set
    user_settings = await settings_helper.get_user_settings(userId)
    has_nickname = user_settings and user_settings[0]  # nickname is the first field
    
    if has_nickname:
        # If user has nickname, show missions and games
        items.append([
            InlineKeyboardButton(
                await localization.get_text_for_user(userId, "button_missions"),
                callback_data="missions")
        ])
        items.append([
            InlineKeyboardButton(
                await localization.get_text_for_user(userId, "button_games"),
                callback_data="games")
        ])

    # Check if user is admin and add admin button
    is_admin = await sqllite_helper.is_user_admin(userId)
    if is_admin:
        items.append([
            InlineKeyboardButton(
                await localization.get_text_for_user(userId, "button_admin"),
                callback_data="admin_assign_alliance")
        ])

    # Settings button is always available
    items.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_settings"),
            callback_data="setting")
    ])

    return items


async def setting(userId):
    """Generate settings keyboard for user"""
    settings = await settings_helper.get_user_settings(userId)
    items = []

    if not settings:
        items.append([
            InlineKeyboardButton(
                await localization.get_text_for_user(userId, "button_set_name"),
                callback_data="requestsetname")
        ])
    else:
        # Show current language
        current_language = settings[2] if len(settings) > 2 and settings[2] else 'ru'
        language_text = await localization.get_text_for_user(
            userId, "button_language")
        items.append([
            InlineKeyboardButton(
                f"{language_text}: {current_language}",
                callback_data="changelanguage")
        ])
        
        # Show notification status
        notifications_on = settings[3] if len(settings) > 3 and settings[3] is not None else 1
        notification_status = "ON" if notifications_on == 1 else "OFF"
        notifications_text = await localization.get_text_for_user(
            userId, "button_notifications")
        items.append([
            InlineKeyboardButton(
                f"{notifications_text}: {notification_status}",
                callback_data="togglenotifications")
        ])
        
        if not settings[0]:  # nickname not set
            items.append([
                InlineKeyboardButton(
                    await localization.get_text_for_user(userId, "button_set_name"),
                    callback_data="requestsetname")
            ])
        
        if not settings[1]:  # registered_as not set
            items.append([
                InlineKeyboardButton(
                    await localization.get_text_for_user(userId, "button_registration"),
                    callback_data="registration")
            ])
    
    items.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_back"),
            callback_data="back_to_main")
    ])
    return items

async def missions_list(user_id):
    items = [[]]
    
async def this_week(rule):
    from datetime import timedelta
    
    # Получаем сегодняшнюю дату
    today = dt.today()
    
    # Создаем список дат на следующие 7 дней начиная с сегодня
    menu_values = []
    for i in range(7):
        date = today + timedelta(days=i)
        menu_values.append(date)

    days = [
        [
            InlineKeyboardButton(menu_values[0].strftime("%A %d.%m"), callback_data=menu_values[0].strftime("%c") + ',' + rule),
            InlineKeyboardButton(menu_values[1].strftime("%A %d.%m"), callback_data=menu_values[1].strftime("%c") + ',' + rule)
        ],
        [
            InlineKeyboardButton(menu_values[2].strftime("%A %d.%m"), callback_data=menu_values[2].strftime("%c") + ',' + rule),
            InlineKeyboardButton(menu_values[3].strftime("%A %d.%m"), callback_data=menu_values[3].strftime("%c") + ',' + rule),
            InlineKeyboardButton(menu_values[4].strftime("%A %d.%m"), callback_data=menu_values[4].strftime("%c") + ',' + rule)
        ],
        [
            InlineKeyboardButton(menu_values[5].strftime("%A %d.%m"), callback_data=menu_values[5].strftime("%c") + ',' + rule),
            InlineKeyboardButton(menu_values[6].strftime("%A %d.%m"), callback_data=menu_values[6].strftime("%c") + ',' + rule)
        ]
    ]
    
    return days

async def today_schedule(user_id):
    today = dt.today()
    appointments = await sqllite_helper.get_schedule_with_warmasters(user_id, str(today.date()))
    buttons = [*map(lambda ap: InlineKeyboardButton(f'{ap[1]} {ap[2]}', callback_data=f'mission_sch_{ap[0]}'),appointments)]
    
    return [[button] for button in buttons]


async def language_selection(userId):
    languages = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru")],
        [InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_back"),
            callback_data="back_to_settings")]
    ]
    return languages


async def admin_assign_alliance_players(userId):
    """Generate keyboard showing players with nicknames for alliance assignment.
    
    Args:
        userId: User telegram ID (admin)
        
    Returns:
        List of button rows for InlineKeyboardMarkup
    """
    players = await sqllite_helper.get_warmasters_with_nicknames()
    buttons = []
    
    for player in players:
        telegram_id, nickname, alliance = player
        # Get alliance name if set
        alliance_name = ""
        if alliance:
            alliances = await sqllite_helper.get_all_alliances()
            for a_id, a_name in alliances:
                if a_id == alliance:
                    alliance_name = f" ({a_name})"
                    break
        
        buttons.append([
            InlineKeyboardButton(
                f"{nickname}{alliance_name}",
                callback_data=f"admin_player:{telegram_id}"
            )
        ])
    
    # Add back button
    buttons.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_back"),
            callback_data="back_to_main"
        )
    ])
    
    return buttons


async def admin_assign_alliance_list(userId, player_telegram_id):
    """Generate keyboard showing alliances for assignment to a player.
    
    Args:
        userId: User telegram ID (admin)
        player_telegram_id: The player to assign alliance to
        
    Returns:
        List of button rows for InlineKeyboardMarkup
    """
    alliances = await sqllite_helper.get_all_alliances()
    buttons = []
    
    for alliance_id, alliance_name in alliances:
        player_count = await sqllite_helper.get_alliance_player_count(alliance_id)
        buttons.append([
            InlineKeyboardButton(
                f"{alliance_name} ({player_count} игроков)",
                callback_data=f"admin_alliance:{player_telegram_id}:{alliance_id}"
            )
        ])
    
    # Add back button
    buttons.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_back"),
            callback_data="admin_assign_alliance"
        )
    ])
    
    return buttons