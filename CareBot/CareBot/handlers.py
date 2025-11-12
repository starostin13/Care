#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8
import notification_service
import localization
import migrate_db
import mission_helper
import logging
import keyboard_constructor
import players_helper
import config
import map_helper
import warmaster_helper
import settings_helper
import schedule_helper
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, Update
from datetime import datetime
import re
import tracemalloc
tracemalloc.start()


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

MAIN_MENU, SETTINGS, GAMES, SCHEDULE, MISSIONS = range(5)
# Callback data
ONE, TWO, THREE, FOUR = range(4)
TYPING_CHOICE, TYPING_REPLY = range(2)


async def appoint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userId = update.effective_user.id
    rules = await keyboard_constructor.get_keyboard_rules_keyboard_for_user(userId)
    menu = InlineKeyboardMarkup(rules)
    await update.message.reply_text(f'Choose the rules {update.effective_user.first_name}', reply_markup=menu)


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    con_keyboard = KeyboardButton(text="send_contact", request_contact=True)
    custom_keyboard = [[con_keyboard]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)

    await update.message.reply_text(
        text="Are you agree to share YOUR PHONE NUMBER? This is MANDATORY to participate in crusade.",
        reply_markup=reply_markup)


async def contact_callback(update, bot):
    contact = update.message.contact
    phone = contact.phone_number
    userid = contact.user_id
    await warmaster_helper.register_warmaster(userid, phone)


async def get_the_mission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # update.callback_query.data 'mission_sch_2'
    mission_number = int(
        update.callback_query.data.replace("mission_sch_", ""))
    rules = await schedule_helper.get_mission_rules(mission_number)
    # Получаем миссию из базы данных
    mission = await mission_helper.get_mission(rules=rules)
    query = update.callback_query
    data = query.data  # Получаем данные из нажатой кнопки
    index_of_mission_id = 2

    # Получаем список всех участников события
    participants = await schedule_helper.get_event_participants(data.rsplit('_', 1)[-1])

    battle_id = await mission_helper.start_battle(mission[index_of_mission_id], participants)
    situation = await mission_helper.get_situation(battle_id, participants)

    # Преобразуем миссию в текст
    text = '\n'.join(
        f'#{mission[i]}' if i == index_of_mission_id else str(item or '')
        for i, item in enumerate(mission)
    )

    # Отправляем текст миссии текущему пользователю
    await query.edit_message_text(f"{text}\n{situation}\nЧто бы укзать результат игры 'ответьте' на это сообщение указав счёт в формате [ваши очки] [очки оппонента], например:\n20 0")

    # Рассылаем сообщение с миссией всем участникам
    for participant_id in participants:
        # Исключаем текущего пользователя
        if participant_id[0] != str(update.effective_user.id):
            try:
                await context.bot.send_message(chat_id=participant_id[0], text=f"Новая миссия:\n{text}")
            except Exception as e:
                logger.error(
                    f"Ошибка при отправке сообщения пользователю {participant_id}: {e}")

    return MISSIONS


async def back_to_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle 'Back' button from language selection"""
    userId = update.effective_user.id
    logger.info(f"back_to_settings called by user {userId}")

    query = update.callback_query
    await query.answer()

    menu = await keyboard_constructor.setting(userId)
    menu_markup = InlineKeyboardMarkup(menu)

    settings_text = await localization.get_text_for_user(userId, "settings_title")
    await query.edit_message_text(settings_text, reply_markup=menu_markup)
    logger.info("Successfully returned to settings menu")
    return SETTINGS


async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle 'Back' button from settings menu"""
    userId = update.effective_user.id
    logger.info(f"back_to_main_menu called by user {userId}")

    query = update.callback_query
    await query.answer()

    menu = await keyboard_constructor.get_main_menu(userId)
    menu_markup = InlineKeyboardMarkup(menu)

    # Check if user has nickname to show appropriate message
    user_settings = await settings_helper.get_user_settings(userId)
    has_nickname = user_settings and user_settings[0]
    user_name = update.effective_user.first_name or "User"
    
    if has_nickname:
        greeting_text = await localization.get_text_for_user(
            userId, 'main_menu_greeting', name=user_name
        )
    else:
        greeting_text = await localization.get_text_for_user(
            userId, 'main_menu_nickname_required', name=user_name
        )

    await query.edit_message_text(greeting_text, reply_markup=menu_markup)
    logger.info("Successfully returned to main menu")
    return MAIN_MENU


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userId = update.effective_user.id
    logger.info(f"hello function called by user {userId}")

    await players_helper.add_warmaster(userId)
    
    # Ensure first user is admin
    import sqllite_helper
    admin_id = await sqllite_helper.ensure_first_user_is_admin()
    if admin_id:
        logger.info(f"Made user {admin_id} an admin (first warmaster)")
    
    menu = await keyboard_constructor.get_main_menu(userId)
    menu_markup = InlineKeyboardMarkup(menu)

    # Check if user has nickname to show appropriate message
    user_settings = await settings_helper.get_user_settings(userId)
    has_nickname = user_settings and user_settings[0]
    user_name = update.effective_user.first_name or "User"
    
    if has_nickname:
        greeting_text = await localization.get_text_for_user(
            userId, 'main_menu_greeting', name=user_name
        )
    else:
        greeting_text = await localization.get_text_for_user(
            userId, 'main_menu_nickname_required', name=user_name
        )

    if update.callback_query:
        # This is a callback query (from "Back" button)
        query = update.callback_query
        logger.info(f"Processing callback query: {query.data}")
        await query.answer()
        await query.edit_message_text(greeting_text, reply_markup=menu_markup)
        logger.info("Successfully processed callback query and updated message")
    else:
        # This is a regular message (from /start command)
        logger.info("Processing regular message")
        await update.message.reply_text(greeting_text, reply_markup=menu_markup)
        logger.info("Successfully sent reply to message")

    logger.info(f"Returning to MAIN_MENU state")
    return MAIN_MENU


async def appoint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userId = update.effective_user.id
    query = update.callback_query
    rules = await keyboard_constructor.get_keyboard_rules_keyboard_for_user(userId)
    menu = InlineKeyboardMarkup(rules)
    await query.edit_message_text(f'Choose the rules {update.effective_user.first_name}', reply_markup=menu)
    return GAMES


async def im_in(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    data = query.data
    data_arr = data.split(',')
    # ['Sat Apr 27 00:00:00 2024', 'rule:killteam']

    game_date = data_arr[0]
    game_rules = data_arr[1].split(':')[1]
    user_id = update.effective_user.id

    # Register player for the game
    await schedule_helper.register_for_game(
        datetime.strptime(game_date, '%c'),
        game_rules,
        user_id)

    # Get opponents
    opponents = await players_helper.get_opponents(user_id, data)
    await query.answer()

    # Send response to the player who just registered
    if len(opponents) == 0:
        await query.edit_message_text('Ещё никто не запился на этот день')
    else:
        await query.edit_message_text('You will faced with')
        for opponent in opponents:
            if opponent[1] is not None:
                await update.effective_chat.send_contact(
                    first_name=str(opponent[0]),
                    phone_number=opponent[1]
                )

    # Notify players about new participant
    await notification_service.notify_players_about_game(
        context, user_id, game_date, game_rules
    )

    return MAIN_MENU


async def end_poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """End the poll and show opponents"""
    await update.message.reply_text('You faced')
    return SETTINGS


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    when_markup = await keyboard_constructor.this_week(query.data)
    menu = InlineKeyboardMarkup(when_markup)
    await query.edit_message_text(
        text=f"Selected option: {query.data}", reply_markup=menu
    )
    return SCHEDULE


async def handle_mission_reply(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handler to process the reply to the message from show_missions"""
    # Retrieve the original message's text and user's reply
    original_message = update.message.reply_to_message.text
    user_reply = update.message.text

    logger.info(
        "User %s replied to '%s' with '%s'",
        update.effective_user.id, original_message, user_reply)

    # Разделяем текст на строки
    lines = original_message.splitlines()

    # Ищем строку, начинающуюся с '#'
    battle_id_line = next(
        (line for line in lines if line.startswith('#')), None)
    if battle_id_line:
        # Извлекаем значение после решётки и преобразуем его в число
        battle_id = int(battle_id_line[1:])
        await mission_helper.write_battle_result(battle_id, user_reply)

        # Apply mission-specific rewards
        rewards = await mission_helper.apply_mission_rewards(battle_id, user_reply, update.effective_user.id)
        scenario_line = next(
            (line for line in lines if line.startswith('📜')), None)
        scenario_name_regexp_result = re.search(
            r"📜(.*?)\:", scenario_line) if scenario_line else None
        scenario = None
        if scenario_name_regexp_result:
            scenario = scenario_name_regexp_result.group(1)

        # Update the map based on battle results
        await map_helper.update_map(
            battle_id,
            user_reply,
            update.effective_user.id,
            scenario
        )

    # Respond to the user's reply
    await update.message.reply_text(f"Сообщение получено: {user_reply}. Отправлено на обработку.")


async def input_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    full_text = update.message.text
    logger.info(f"input_name function called by user {user_id} with text: '{full_text}'")
    
    # Handle /setname command with parameter
    text_parts = full_text.split(' ', 1)
    logger.info(f"Split text into parts: {text_parts}")
    
    if len(text_parts) > 1:
        text = text_parts[1]
        logger.info(f"Setting name '{text}' for user {user_id} via /setname command")
        await players_helper.set_name(user_id, text)
        await update.message.reply_text(f"Your {text}? Yes, I would love to hear about that!")
        logger.info(f"Successfully set name via /setname command for user {user_id}")
    else:
        logger.warning(f"User {user_id} used /setname without providing a name")
        await update.message.reply_text("Please provide a name after the command, for example: /setname YourName")


async def registration_call(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        'Just type or click on it /regme'
    )


async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    query = update.callback_query
    logger.info(f"set_name function called by user {user_id}, callback_data: {query.data}")
    
    await query.answer()
    
    # Get localized text for name input prompt
    prompt_text = await localization.get_text_for_user(user_id, "enter_name_prompt")
    logger.info(f"Sending name input prompt to user {user_id}: {prompt_text}")
    
    # Instead of changing state, send a message requesting reply
    back_button = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            await localization.get_text_for_user(user_id, "button_back"),
            callback_data="setting"
        )
    ]])
    
    await query.edit_message_text(
        f"{prompt_text}\n\n⚠️ Просто напишите ваше имя следующим сообщением",
        reply_markup=back_button
    )
    
    # Store that user is waiting for name input
    context.user_data['waiting_for_name'] = True
    logger.info(f"Set waiting_for_name flag for user {user_id}")
    
    return SETTINGS  # Stay in SETTINGS state


async def setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    logger.info(f"setting function called by user {user_id}")
    
    menu = await keyboard_constructor.setting(user_id)
    query = update.callback_query
    await query.answer()
    markup = InlineKeyboardMarkup(menu)

    settings_text = await localization.get_text_for_user(user_id, "settings_title")
    await query.edit_message_text(settings_text, reply_markup=markup)
    logger.info(f"Returning to SETTINGS state for user {user_id}")
    return SETTINGS


async def show_missions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    menu = await keyboard_constructor.today_schedule(user_id)
    markup = InlineKeyboardMarkup(menu)
    query = update.callback_query

    appointments_text = await localization.get_text_for_user(user_id, "appointments_title")
    await query.edit_message_text(appointments_text, reply_markup=markup)
    return MISSIONS


async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    menu = await keyboard_constructor.language_selection(user_id)
    query = update.callback_query
    await query.answer()
    markup = InlineKeyboardMarkup(menu)

    select_lang_text = await localization.get_text_for_user(user_id, "select_language")
    await query.edit_message_text(select_lang_text, reply_markup=markup)
    return MAIN_MENU


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    language = query.data.split(':')[1]
    user_id = update.effective_user.id
    await settings_helper.set_user_language(user_id, language)
    await query.answer()

    # Return to settings
    menu = await keyboard_constructor.setting(user_id)
    markup = InlineKeyboardMarkup(menu)

    lang_updated_text = await localization.get_text_for_user(user_id, "language_updated")
    await query.edit_message_text(lang_updated_text, reply_markup=markup)
    return SETTINGS


async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = update.effective_user.id
    new_value = await settings_helper.toggle_user_notifications(user_id)
    await query.answer()

    status_key = "notifications_enabled" if new_value == 1 else "notifications_disabled"
    status_text = await localization.get_text_for_user(user_id, status_key)

    # Return to settings
    menu = await keyboard_constructor.setting(user_id)
    markup = InlineKeyboardMarkup(menu)

    settings_text = await localization.get_text_for_user(user_id, "settings_title")
    message = f"Weekday notifications {status_text}! {settings_text}"
    await query.edit_message_text(message, reply_markup=markup)
    return SETTINGS


async def handle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user name input - DEPRECATED, use handle_text_message instead."""
    user_id = update.effective_user.id
    name = update.message.text.strip()
    
    logger.info(f"handle_name_input DEPRECATED called by user {user_id} with name: '{name}'")
    
    if not name or len(name) > 50:
        logger.warning(f"Invalid name input from user {user_id}: name='{name}', length={len(name) if name else 0}")
        error_text = await localization.get_text_for_user(user_id, "invalid_name_error")
        await update.message.reply_text(error_text)
        logger.info(f"Sent invalid name error to user {user_id}")
        return ConversationHandler.END
    
    # Set the name
    logger.info(f"Setting name '{name}' for user {user_id}")
    await players_helper.set_name(user_id, name)
    logger.info(f"Successfully set name for user {user_id}")
    
    # Send confirmation and return to main menu
    success_text = await localization.get_text_for_user(user_id, "name_set_success", name=name)
    
    # Create main menu
    menu = await keyboard_constructor.get_main_menu(user_id)
    menu_markup = InlineKeyboardMarkup(menu)
    
    # Get greeting text
    user_settings = await settings_helper.get_user_settings(user_id)
    user_name = update.effective_user.first_name or "User"
    greeting_text = await localization.get_text_for_user(
        user_id, 'main_menu_greeting', name=user_name
    )
    
    logger.info(f"Sending success confirmation to user {user_id} and returning to MAIN_MENU")
    await update.message.reply_text(f"{success_text}\n\n{greeting_text}", reply_markup=menu_markup)
    logger.info(f"Successfully completed name setting process for user {user_id}")
    return MAIN_MENU


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle any text message - check if user is waiting for name input"""
    user_id = update.effective_user.id
    
    # Check if user is waiting for name input
    if context.user_data.get('waiting_for_name', False):
        logger.info(f"Processing name input from user {user_id}")
        context.user_data['waiting_for_name'] = False  # Clear flag
        
        name = update.message.text.strip()
        
        if not name or len(name) > 50 or len(name) < 2:
            logger.warning(f"Invalid name input from user {user_id}: '{name}'")
            error_text = await localization.get_text_for_user(user_id, "invalid_name_error")
            await update.message.reply_text(error_text)
            return ConversationHandler.END
        
        # Set the name
        logger.info(f"Setting name '{name}' for user {user_id}")
        await players_helper.set_name(user_id, name)
        
        # Send confirmation
        success_text = await localization.get_text_for_user(user_id, "name_set_success", name=name)
        await update.message.reply_text(success_text)
        
        logger.info(f"Successfully set name '{name}' for user {user_id}")
        return ConversationHandler.END
    
    # If not waiting for name, show welcome message
    await welcome(update, context)
    return ConversationHandler.END


async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to the Crusade Bot! Please type /start to begin.")


async def admin_assign_alliance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of players for admin to assign alliance."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    # Check if user is admin
    import sqllite_helper
    is_admin = await sqllite_helper.is_user_admin(user_id)
    if not is_admin:
        await query.edit_message_text("У вас нет прав администратора.")
        return MAIN_MENU
    
    # Get keyboard with players
    menu = await keyboard_constructor.admin_assign_alliance_players(user_id)
    markup = InlineKeyboardMarkup(menu)
    
    admin_text = await localization.get_text_for_user(user_id, "admin_assign_alliance_title")
    await query.edit_message_text(admin_text, reply_markup=markup)
    return MAIN_MENU


async def admin_select_player(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Admin selected a player, now show alliance list."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    # Extract player telegram ID from callback data
    player_telegram_id = query.data.split(':')[1]
    
    # Get player nickname
    import sqllite_helper
    nickname = await sqllite_helper.get_nicknamane(player_telegram_id)
    
    # Get keyboard with alliances
    menu = await keyboard_constructor.admin_assign_alliance_list(user_id, player_telegram_id)
    markup = InlineKeyboardMarkup(menu)
    
    select_alliance_text = await localization.get_text_for_user(
        user_id, "admin_select_alliance_for_player", player_name=nickname
    )
    await query.edit_message_text(select_alliance_text, reply_markup=markup)
    return MAIN_MENU


async def admin_assign_alliance_to_player(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Admin assigned alliance to player."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    # Extract player telegram ID and alliance ID from callback data
    parts = query.data.split(':')
    player_telegram_id = parts[1]
    alliance_id = int(parts[2])
    
    # Assign alliance
    import sqllite_helper
    await sqllite_helper.set_warmaster_alliance(player_telegram_id, alliance_id)
    
    # Get player and alliance names for confirmation
    nickname = await sqllite_helper.get_nicknamane(player_telegram_id)
    alliances = await sqllite_helper.get_all_alliances()
    alliance_name = ""
    for a_id, a_name in alliances:
        if a_id == alliance_id:
            alliance_name = a_name
            break
    
    # Show confirmation and return to main menu
    success_text = await localization.get_text_for_user(
        user_id, "admin_alliance_assigned", 
        player_name=nickname, alliance_name=alliance_name
    )
    await query.edit_message_text(success_text)
    
    # Return to main menu after a moment
    menu = await keyboard_constructor.get_main_menu(user_id)
    menu_markup = InlineKeyboardMarkup(menu)
    
    greeting_text = await localization.get_text_for_user(
        user_id, 'main_menu_greeting', name=update.effective_user.first_name or "User"
    )
    await context.bot.send_message(
        chat_id=user_id,
        text=greeting_text,
        reply_markup=menu_markup
    )
    
    return MAIN_MENU


async def debug_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug handler for unmatched callbacks"""
    query = update.callback_query
    user_id = update.effective_user.id
    logger.warning(f"Unmatched callback from user {user_id}: '{query.data}'")
    await query.answer()
    return ConversationHandler.END

# Run database migrations before starting the bot
print("🔄 Checking for pending database migrations...")
migration_success = migrate_db.run_migrations()
if not migration_success:
    print("❌ Database migration failed! Bot cannot start.")
    exit(1)
print("✅ Database migrations completed successfully.")

bot = ApplicationBuilder().token(config.crusade_care_bot_telegram_token).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", hello),
                  ],
    states={
        MAIN_MENU: [
            CallbackQueryHandler(set_name, pattern='^requestsetname$'),
            CallbackQueryHandler(setting, pattern='^setting$'),
            CallbackQueryHandler(setting, pattern='^callsettings$'),
            CallbackQueryHandler(appoint, pattern='^games$'),
            CallbackQueryHandler(appoint, pattern="^" + 'callgame' + "$"),
            CallbackQueryHandler(show_missions, pattern='^missions$'),
            CallbackQueryHandler(registration_call, pattern='^registration$'),
            CallbackQueryHandler(show_missions, pattern='^callmissions$'),
            CallbackQueryHandler(change_language, pattern='^changelanguage$'),
            CallbackQueryHandler(set_language, pattern='^lang:'),
            CallbackQueryHandler(toggle_notifications,
                                 pattern='^togglenotifications$'),
            CallbackQueryHandler(
                back_to_settings, pattern='^back_to_settings$'),
            # Admin handlers
            CallbackQueryHandler(admin_assign_alliance, pattern='^admin_assign_alliance$'),
            CallbackQueryHandler(admin_select_player, pattern='^admin_player:'),
            CallbackQueryHandler(admin_assign_alliance_to_player, pattern='^admin_alliance:')
        ],
        SETTINGS: [
            CallbackQueryHandler(back_to_main_menu, pattern='^back_to_main$'),
            CallbackQueryHandler(back_to_main_menu, pattern='^start$'),
            CallbackQueryHandler(set_name, pattern='^requestsetname$'),
            CallbackQueryHandler(change_language, pattern='^changelanguage$'),
            CallbackQueryHandler(set_language, pattern='^lang:'),
            CallbackQueryHandler(toggle_notifications,
                                 pattern='^togglenotifications$'),
            CallbackQueryHandler(debug_callback)  # Catch all unmatched callbacks
        ],
        GAMES: [
            CallbackQueryHandler(hello, pattern='^start$'),
            CallbackQueryHandler(button, pattern='rule')
        ],
        SCHEDULE: [
            CallbackQueryHandler(hello, pattern='^start$'),
            # Matches date,rule:rulename format
            CallbackQueryHandler(im_in, pattern=r'^.+,rule:.+$')
        ],
        MISSIONS: [
            CallbackQueryHandler(hello, pattern='^start$'),
            CallbackQueryHandler(get_the_mission)
        ]
    },
    fallbacks=[CommandHandler("start", hello)],
)

# Handler for catching replies to the bot's messages, specifically replies to
# get_the_mission
bot.add_handler(
    MessageHandler(filters.REPLY & filters.TEXT, handle_mission_reply)
)
bot.add_handler(conv_handler)
bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
bot.add_handler(CommandHandler("setname", input_name))
bot.add_handler(CommandHandler("regme", contact))
bot.add_handler(MessageHandler(filters.CONTACT, contact_callback))

bot.run_polling()
