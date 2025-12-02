from datetime import datetime as dt
from telegram import InlineKeyboardButton

import settings_helper
import schedule_helper
import localization
import config

# Автоматическое переключение на mock версию в тестовом режиме
if config.TEST_MODE:
    import mock_sqlite_helper as sqllite_helper
    print("🧪 Keyboard Constructor using MOCK SQLite helper")
else:
    import sqllite_helper
    print("✅ Keyboard Constructor using REAL SQLite helper")

async def get_keyboard_rules_keyboard_for_user(user_telegram: str):    
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

    # Check if user is admin and add admin buttons
    is_admin = await sqllite_helper.is_user_admin(userId)
    print(f"DEBUG: User {userId} is_admin check: {is_admin}")  # Debug log
    if is_admin:
        admin_button_text = await localization.get_text_for_user(userId, "button_admin")
        print(f"DEBUG: Adding admin button with text: {admin_button_text}")  # Debug log
        items.append([
            InlineKeyboardButton(
                admin_button_text,
                callback_data="admin_menu")
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
    
async def this_week(rule, user_id):
    from datetime import timedelta
    
    # Получаем сегодняшнюю дату
    today = dt.today()
    
    # Создаем список дат на следующие 7 дней начиная с сегодня
    menu_values = []
    for i in range(7):
        date = today + timedelta(days=i)
        menu_values.append(date)

    # Разделяем дни на выходные (суббота=5, воскресенье=6) и будни
    weekend_days = []
    weekdays = []
    
    for date in menu_values:
        if date.weekday() in [5, 6]:  # Saturday=5, Sunday=6
            weekend_days.append(date)
        else:
            weekdays.append(date)
    
    # Создаем кнопки для дней
    days = []
    
    # Первый ряд: выходные дни (всегда первыми с выделением)
    if weekend_days:
        weekend_row = []
        for date in weekend_days:
            # Добавляем эмодзи 🔵 для выделения выходных
            button_text = f"🔵 {date.strftime('%A %d.%m')}"
            weekend_row.append(
                InlineKeyboardButton(button_text, callback_data=date.strftime("%c") + ',' + rule)
            )
        days.append(weekend_row)
    
    # Остальные ряды: будни (по 2-3 кнопки в ряду)
    weekday_buttons = []
    for date in weekdays:
        weekday_buttons.append(
            InlineKeyboardButton(date.strftime("%A %d.%m"), callback_data=date.strftime("%c") + ',' + rule)
        )
    
    # Распределяем будни по рядам (по 2-3 кнопки)
    i = 0
    while i < len(weekday_buttons):
        # Если осталось 3 или меньше кнопок, размещаем их в одном ряду
        if len(weekday_buttons) - i <= 3:
            days.append(weekday_buttons[i:])
            break
        # Иначе размещаем по 2 кнопки в ряду
        else:
            days.append(weekday_buttons[i:i+2])
            i += 2
    
    # Добавляем кнопку "Назад" как отдельный ряд
    days.append([InlineKeyboardButton(
                await localization.get_text_for_user(user_id, "button_back"),
                callback_data="back_to_games")])
    
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


async def admin_appoint_admin_users(userId):
    """Generate keyboard showing users with nicknames for admin appointment.
    
    Args:
        userId: User telegram ID (admin)
        
    Returns:
        List of button rows for InlineKeyboardMarkup
    """
    players = await sqllite_helper.get_warmasters_with_nicknames()
    buttons = []
    
    for player in players:
        telegram_id, nickname, alliance = player
        # Check if user is already admin
        is_admin = await sqllite_helper.is_user_admin(telegram_id)
        admin_badge = " ⭐" if is_admin else ""
        
        buttons.append([
            InlineKeyboardButton(
                f"{nickname}{admin_badge}",
                callback_data=f"admin_make_admin:{telegram_id}"
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


async def get_admin_menu(userId):
    """Generate admin menu keyboard"""
    items = []
    
    # Player alliance assignment (existing functionality)
    items.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_admin_assign_alliance"),
            callback_data="admin_assign_alliance")
    ])
    
    # Admin appointment (existing functionality)
    items.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_appoint_admin"),
            callback_data="admin_appoint_admin")
    ])
    
    # Alliance management (new functionality)
    items.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_admin_alliance_management"),
            callback_data="admin_alliance_management")
    ])
    
    # Back to main menu
    items.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_back"),
            callback_data="back_to_main")
    ])
    
    return items


async def get_alliance_management_menu(userId):
    """Generate alliance management menu keyboard"""
    items = []
    
    # Create new alliance
    items.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_create_alliance"),
            callback_data="admin_create_alliance")
    ])
    
    # Edit existing alliances
    items.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_edit_alliances"),
            callback_data="admin_edit_alliances")
    ])
    
    # Delete alliances
    items.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_delete_alliances"),
            callback_data="admin_delete_alliances")
    ])
    
    # Back to admin menu
    items.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_back"),
            callback_data="admin_menu")
    ])
    
    return items


async def get_alliance_list_for_edit(userId):
    """Generate keyboard with list of alliances for editing"""
    items = []
    
    alliances = await sqllite_helper.get_all_alliances()
    for alliance in alliances:
        alliance_id = alliance[0]
        alliance_name = alliance[1]
        # Show alliance name and player count
        player_count = await sqllite_helper.get_alliance_player_count(alliance_id)
        display_text = f"{alliance_name} ({player_count})"
        
        items.append([
            InlineKeyboardButton(
                display_text,
                callback_data=f"admin_edit_alliance:{alliance_id}")
        ])
    
    # Back button
    items.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_back"),
            callback_data="admin_alliance_management")
    ])
    
    return items


async def get_alliance_list_for_delete(userId):
    """Generate keyboard with list of alliances for deletion"""
    items = []
    
    alliances = await sqllite_helper.get_all_alliances()
    for alliance in alliances:
        alliance_id = alliance[0]
        alliance_name = alliance[1]
        # Show alliance name and player count
        player_count = await sqllite_helper.get_alliance_player_count(alliance_id)
        display_text = f"{alliance_name} ({player_count})"
        
        items.append([
            InlineKeyboardButton(
                display_text,
                callback_data=f"admin_delete_alliance:{alliance_id}")
        ])
    
    # Back button
    items.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_back"),
            callback_data="admin_alliance_management")
    ])
    
    return items


async def get_alliance_confirmation_keyboard(userId, action, alliance_id, alliance_name=""):
    """Generate confirmation keyboard for alliance operations
    
    Args:
        userId: User telegram ID
        action: "delete" or "edit"
        alliance_id: ID of alliance
        alliance_name: Name of alliance (for display)
    """
    items = []
    
    if action == "delete":
        # Confirm deletion
        items.append([
            InlineKeyboardButton(
                await localization.get_text_for_user(userId, "button_confirm_delete"),
                callback_data=f"admin_confirm_delete:{alliance_id}")
        ])
        
        # Cancel
        items.append([
            InlineKeyboardButton(
                await localization.get_text_for_user(userId, "button_cancel"),
                callback_data="admin_delete_alliances")
        ])
    
    elif action == "edit":
        # Rename alliance
        items.append([
            InlineKeyboardButton(
                await localization.get_text_for_user(userId, "button_rename_alliance"),
                callback_data=f"admin_rename_alliance:{alliance_id}")
        ])
        
        # Back to edit list
        items.append([
            InlineKeyboardButton(
                await localization.get_text_for_user(userId, "button_back"),
                callback_data="admin_edit_alliances")
        ])
    
    return items