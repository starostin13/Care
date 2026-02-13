from datetime import datetime as dt
from telegram import InlineKeyboardButton
import random

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

# Emoji arrays for participant count display
EMOJI_1_PERSON = ['👤', '🧑', '😗', '😎', '🫅', '👹', '👺', '👽', '🤖', '😼', '🐺', '🧟', '🧌', '🤺', '🥷', '🦹', '🧙', '🧚', '🧛', '🧝', '🙎', '🙋', '🧍', '🕺', '🪖', '🚼', '⚜️', '🚹', '1️⃣']
EMOJI_2_PERSONS = ['👫', '👬', '🫂', '👯', '👭', '👥', '✌️', '🤼', '🤼‍♂️', '🧑🏻‍🤝‍🧑🏼', '🎎', '🎭', '🚸', '2️⃣']
EMOJI_3_PERSONS = ['👫👤', '👥👤', '3️⃣']
EMOJI_4_PERSONS = ['👫👫', '👥👥', '4️⃣']
EMOJI_5_PERSONS = ['👫👫👤', '👥👤', '5️⃣']
EMOJI_6_PERSONS = ['👫👫👫', '👥👥👥', '6️⃣']
EMOJI_7_PLUS = ['🎉', '🎊', '🎈', '👥👥👥👥', '🎪', '🎆', '🎇', '6️⃣➕']

# Short weekday labels are now loaded from database via localization
async def get_day_abbreviations(language='ru'):
    """Get localized day abbreviations from database."""
    days = []
    day_keys = [
        'day_monday_short',
        'day_tuesday_short', 
        'day_wednesday_short',
        'day_thursday_short',
        'day_friday_short',
        'day_saturday_short',
        'day_sunday_short'
    ]
    for key in day_keys:
        day_text = await localization.get_text(key, language)
        days.append(day_text)
    return days


def get_participant_count_emoji(count: int) -> str:
    """Return random emoji based on participant count.
    Returns empty string if count is 0 (no participants).
    """
    if count == 0:
        return ""
    elif count == 1:
        return f" {random.choice(EMOJI_1_PERSON)}"
    elif count == 2:
        return f" {random.choice(EMOJI_2_PERSONS)}"
    elif count == 3:
        return f" {random.choice(EMOJI_3_PERSONS)}"
    elif count == 4:
        return f" {random.choice(EMOJI_4_PERSONS)}"
    elif count == 5:
        return f" {random.choice(EMOJI_5_PERSONS)}"
    elif count == 6:
        return f" {random.choice(EMOJI_6_PERSONS)}"
    else:  # 7+
        return f" {random.choice(EMOJI_7_PLUS)}"

async def get_keyboard_rules_keyboard_for_user(user_telegram: str):
    # Get current week number (ISO week)
    current_week = dt.now().isocalendar()[1]
    
    rules = [
        ("Kill Team", "killteam"),
        ("Boarding Action", "boardingaction"),
        ("WH40k 10", "wh40k"),
        ("Combat patrol", "combatpatrol"),
        ("Battlefleet", "battlefleet"),
    ]
    
    # Get participant counts for all rules in a single database query
    rule_keys = [rule_key for _, rule_key in rules]
    counts = await sqllite_helper.get_weekly_rule_participant_counts(rule_keys, current_week)
    
    buttons = []
    for rule_name, rule_key in rules:
        count = counts.get(rule_key, 0)
        emoji = get_participant_count_emoji(count)
        
        button_text = f"{rule_name}{emoji}"
        buttons.append([InlineKeyboardButton(button_text, callback_data=f"rule:{rule_key}")])
    
    return buttons

async def get_main_menu(userId):
    items = []
    
    # Check if user has a nickname set
    user_settings = await settings_helper.get_user_settings(userId)
    has_nickname = user_settings and user_settings[0]  # nickname is the first field
    alliance = await sqllite_helper.get_alliance_of_warmaster(userId)
    has_alliance = alliance and alliance[0] not in (None, 0)
    
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

    if has_alliance:
        items.append([
            InlineKeyboardButton(
                await localization.get_text_for_user(userId, "button_alliance_resources"),
                callback_data="alliance_resources")
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

    # Определяем язык и короткие названия дней недели
    user_lang = await localization.get_user_language(user_id)
    day_abbr = await get_day_abbreviations(user_lang)

    def format_day(date_obj):
        return f"{day_abbr[date_obj.weekday()]} {date_obj.strftime('%d.%m')}"
    
    async def create_day_button(date, user_bookings, rule):
        """Helper function to create a calendar day button.
        
        Args:
            date: datetime object for the day
            user_bookings: dict mapping date strings to rule names
            rule: current rule being displayed
            
        Returns:
            InlineKeyboardButton for the day
        """
        date_str = str(date.date())
        count = await sqllite_helper.get_daily_rule_participant_count(rule, date_str)
        emoji = get_participant_count_emoji(count)
        
        # Check if user is booked for other rules on this date
        is_booked_for_other_rule = date_str in user_bookings and user_bookings[date_str] != rule
        
        # Add blue circle only if user is booked for a different rule
        prefix = "🔵 " if is_booked_for_other_rule else ""
        button_text = f"{prefix}{format_day(date)}{emoji}"
        
        return InlineKeyboardButton(
            button_text,
            callback_data=f"{date.strftime('%c')},rule:{rule}"
        )
    
    # Создаем список дат на следующие 7 дней начиная с сегодня
    menu_values = []
    for i in range(7):
        date = today + timedelta(days=i)
        menu_values.append(date)

    # Get user's existing bookings for all dates in the week
    date_strs = [str(date.date()) for date in menu_values]
    user_bookings = await sqllite_helper.get_user_bookings_for_dates(user_id, date_strs)

    # Разделяем дни на выходные (суббота=5, воскресенье=6) и будни
    weekend_days = []
    weekdays = []
    
    for date in menu_values:
        date_str = str(date.date())
        # Skip dates where user is already booked for the selected rule
        if date_str in user_bookings and user_bookings[date_str] == rule:
            continue
            
        if date.weekday() in [5, 6]:  # Saturday=5, Sunday=6
            weekend_days.append(date)
        else:
            weekdays.append(date)
    
    # Создаем кнопки для дней
    days = []
    
    # Первый ряд: выходные дни (всегда первыми, без выделения)
    if weekend_days:
        weekend_row = []
        for date in weekend_days:
            button = await create_day_button(date, user_bookings, rule)
            weekend_row.append(button)
        days.append(weekend_row)
    
    # Остальные ряды: будни (по 2-3 кнопки в ряду)
    weekday_buttons = []
    for date in weekdays:
        button = await create_day_button(date, user_bookings, rule)
        weekday_buttons.append(button)
    
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
    """Create schedule keyboard with opponent info in callback_data.
    
    appointments format: (schedule_id, rules, opponent_nickname, opponent_telegram_id)
    callback_data format: mission_sch_{schedule_id}_{opponent_telegram_id}
    """
    today = dt.today()
    appointments = await sqllite_helper.get_schedule_with_warmasters(user_id, str(today.date()))
    buttons = [*map(lambda ap: InlineKeyboardButton(f'{ap[1]} {ap[2]}', callback_data=f'mission_sch_{ap[0]}_{ap[3]}'),appointments)]
    
    return [[button] for button in buttons]


async def language_selection(userId):
    russian_label = await localization.get_text("btn_language_russian", "ru")
    languages = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton(russian_label, callback_data="lang:ru")],
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
    
    # Get user language for localized text
    user_lang = await localization.get_user_language(userId)
    
    for alliance_id, alliance_name in alliances:
        player_count = await sqllite_helper.get_alliance_player_count(alliance_id)
        button_text = await localization.get_text(
            "alliance_player_count",
            user_lang,
            alliance_name=alliance_name,
            player_count=player_count
        )
        buttons.append([
            InlineKeyboardButton(
                button_text,
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

    # Alliance resource adjustments
    items.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_admin_adjust_resources"),
            callback_data="admin_adjust_resources")
    ])
    
    # Custom notifications (new functionality)
    items.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_admin_custom_notification"),
            callback_data="admin_custom_notification")
    ])

    # Statistics menu
    items.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_admin_stats"),
            callback_data="admin_stats_menu")
    ])
    
    # Feature flags management
    items.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_admin_feature_flags"),
            callback_data="admin_feature_flags")
    ])
    
    # Pending mission confirmations - only show if there are pending missions
    pending_count = await sqllite_helper.get_pending_missions_count()
    if pending_count > 0:
        user_lang = await localization.get_user_language(userId)
        button_text = await localization.get_text(
            "admin_pending_count",
            user_lang,
            pending_count=pending_count
        )
        items.append([
            InlineKeyboardButton(
                button_text,
                callback_data="admin_pending_confirmations")
        ])
    
    # Back to main menu
    items.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_back"),
            callback_data="back_to_main")
    ])
    
    return items


async def get_admin_stats_menu(userId):
    """Generate admin statistics submenu keyboard."""
    return [
        [
            InlineKeyboardButton(
                await localization.get_text_for_user(userId, "button_admin_stats_users"),
                callback_data="admin_stats_users")
        ],
        [
            InlineKeyboardButton(
                await localization.get_text_for_user(userId, "button_admin_stats_alliances"),
                callback_data="admin_stats_alliances")
        ],
        [
            InlineKeyboardButton(
                await localization.get_text_for_user(userId, "button_back"),
                callback_data="admin_menu")
        ]
    ]


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


async def get_alliance_list_for_resources(userId):
    """Generate keyboard for selecting alliance to adjust resources."""
    items = []
    
    alliances = await sqllite_helper.get_all_alliances_with_resources()
    for alliance_id, alliance_name, resource_amount in alliances:
        display_text = f"{alliance_name} ({resource_amount})"
        items.append([
            InlineKeyboardButton(
                display_text,
                callback_data=f"admin_adjust_alliance:{alliance_id}")
        ])
    
    items.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_back"),
            callback_data="admin_menu")
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


async def get_admin_feature_flags_menu(userId):
    """Generate feature flags management keyboard"""
    import feature_flags_helper
    
    items = []
    
    # Get all feature flags
    flags = await feature_flags_helper.get_all_feature_flags()
    
    for flag_name, enabled, description in flags:
        # Get localized name for the feature
        feature_name_key = f"feature_{flag_name}_name"
        feature_name = await localization.get_text_for_user(userId, feature_name_key)
        
        # Create status indicator
        if enabled:
            status_text = await localization.get_text_for_user(userId, "feature_flag_enabled")
        else:
            status_text = await localization.get_text_for_user(userId, "feature_flag_disabled")
        
        button_text = f"{feature_name}: {status_text}"
        
        items.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"admin_toggle_feature:{flag_name}")
        ])
    
    # Back button
    items.append([
        InlineKeyboardButton(
            await localization.get_text_for_user(userId, "button_back"),
            callback_data="admin_menu")
    ])
    
    return items
