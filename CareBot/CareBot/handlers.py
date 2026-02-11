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
import mission_message_builder
# Автоматическое переключение на mock версию в тестовом режиме
if config.TEST_MODE:
    import mock_sqlite_helper as sqllite_helper
    print("🧪 Handlers using MOCK SQLite helper")
else:
    import sqllite_helper
    print("✅ Handlers using REAL SQLite helper")
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

MAIN_MENU, SETTINGS, GAMES, SCHEDULE, MISSIONS, ALLIANCE_INPUT, CUSTOM_NOTIFICATION = range(7)
# Callback data
ONE, TWO, THREE, FOUR = range(4)
TYPING_CHOICE, TYPING_REPLY = range(2)


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
    # update.callback_query.data 'mission_sch_{schedule_id}_{opponent_telegram_id}'
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query
    
    # Validate callback data - it should start with 'mission_sch_'
    if not query.data.startswith("mission_sch_"):
        logger.error(f"Invalid mission callback data: {query.data}")
        error_msg = await localization.get_text_for_user(update.effective_user.id, "error_invalid_request")
        await query.edit_message_text(error_msg)
        return MISSIONS
    
    try:
        # Parse callback data: mission_sch_{schedule_id}_{opponent_telegram_id}
        data_parts = query.data.replace("mission_sch_", "").split("_")
        mission_number = int(data_parts[0])
        defender_id = str(data_parts[1])  # Opponent telegram_id from callback
    except (ValueError, AttributeError, IndexError) as e:
        logger.error(f"Failed to parse mission callback data '{query.data}': {e}")
        error_msg = await localization.get_text_for_user(update.effective_user.id, "error_mission_info_failed")
        await query.edit_message_text(error_msg)
        return MISSIONS
    
    rules = await schedule_helper.get_mission_rules(mission_number)
    
    # Определяем атакующего (кто нажал кнопку) и защищающегося (из callback_data)
    attacker_id = str(update.effective_user.id)
    logger.info(f"Mission selected: attacker={attacker_id}, defender={defender_id}, rules={rules}")
    
    # Получаем миссию из базы данных с определением cell на основе участников
    mission = await mission_helper.get_mission(rules=rules, attacker_id=attacker_id, defender_id=defender_id)
    # mission_stack schema: [0:deploy, 1:rules, 2:cell, 3:description, 4:id, ...]

    # Извлекаем правильный mission_id из кортежа миссии (он на позиции 4)
    mission_id = mission[4]
    logger.info(f"Mission ID from database: {mission_id}")
    
    # Создаем бой с ровно двумя игроками
    # attacker_id будет fstplayer, defender_id будет sndplayer
    if not defender_id:
        logger.error(
            f"Cannot start battle: no defender found for attacker {attacker_id}")
        error_msg = await localization.get_text_for_user(update.effective_user.id, "error_no_opponent")
        await query.edit_message_text(error_msg)
        return MISSIONS
    
    try:
        battle_id = await mission_helper.start_battle(mission_id, attacker_id, defender_id)
    except ValueError as e:
        logger.error(f"Failed to start battle: {e}")
        error_msg = await localization.get_text_for_user(update.effective_user.id, "error_battle_creation", error=str(e))
        await query.edit_message_text(error_msg)
        return MISSIONS

    # Lock the mission now that battle has been successfully created
    await sqllite_helper.lock_mission(mission_id)

    situation = await mission_helper.get_situation(battle_id, [(attacker_id,), (defender_id,)])
    
    # Check if attacker has reinforcement restrictions
    reinforcement_message = await mission_helper.check_attacker_reinforcement_status(
        battle_id, attacker_id
    )

    # Determine dominant alliance
    dominant_alliance_id = await sqllite_helper.get_dominant_alliance()
    logger.info(f"Dominant alliance: {dominant_alliance_id}")
    
    # Get alliances of both players
    attacker_alliance = await sqllite_helper.get_alliance_of_warmaster(attacker_id)
    defender_alliance = await sqllite_helper.get_alliance_of_warmaster(defender_id)
    
    attacker_alliance_id = attacker_alliance[0] if attacker_alliance else None
    defender_alliance_id = defender_alliance[0] if defender_alliance else None
    
    # Check if either player belongs to dominant alliance
    attacker_is_dominant = (dominant_alliance_id and 
                           attacker_alliance_id == dominant_alliance_id and
                           attacker_alliance_id != 0)
    defender_is_dominant = (dominant_alliance_id and 
                           defender_alliance_id == dominant_alliance_id and
                           defender_alliance_id != 0)
    
    # Get nicknames for messages
    attacker_nickname = await sqllite_helper.get_nicknamane(attacker_id)
    defender_nickname = await sqllite_helper.get_nicknamane(defender_id)
    
    # Формируем текст для пользователя используя message builder
    mission_description = mission[3] or ''
    mission_rules = mission[1] or ''
    # Check if map_description is available (for battlefleet missions)
    # For battlefleet missions, the tuple is: (deploy, rules, cell, description, id, winner_bonus, map_description)
    # So map_description would be at index 6
    map_description = None
    if len(mission) > 6 and mission_rules == "battlefleet":
        map_description = mission[6]
    
    # Get user languages for localized messages
    attacker_lang = await localization.get_user_language(attacker_id)
    defender_lang = await localization.get_user_language(defender_id)
    
    # Helper function to build message for a player
    async def build_mission_message(opponent_is_dominant, opponent_nickname, user_lang):
        builder = mission_message_builder.MissionMessageBuilder(
            mission_id, mission_description, mission_rules, user_lang
        )
        
        # Add extra info from mission tuple (Killzone, PTS info, etc)
        # Indices after 5 are extra info appended by mission_helper.get_mission
        if len(mission) > 6:
            for extra_info in mission[6:]:
                if isinstance(extra_info, str):
                    builder.add_custom_info(extra_info)
        
        # Add double exp bonus if opponent is dominant
        if opponent_is_dominant:
            await builder.add_double_exp_bonus(opponent_nickname)
        
        # Add common components
        builder.add_situation(situation)
        builder.add_reinforcement_message(reinforcement_message)
        
        # Add map description for battlefleet missions
        if map_description:
            builder.add_custom_info(f"\n{map_description}")
        
        return builder.build()
    
    # Build messages for both players
    attacker_message = await build_mission_message(defender_is_dominant, defender_nickname, attacker_lang)
    logger.info(f"Composed mission text for attacker: {attacker_message}")

    # Отправляем текст миссии текущему пользователю (атакующему)
    # Create Back button to return to missions list
    btn_text = await localization.get_text_for_user(update.effective_user.id, "btn_back_to_missions")
    back_button = [[InlineKeyboardButton(btn_text, callback_data="back_to_missions")]]
    back_markup = InlineKeyboardMarkup(back_button)
    
    score_instructions = await localization.get_text_for_user(update.effective_user.id, "mission_score_instructions")
    await query.edit_message_text(
        f"{attacker_message}\n{score_instructions}",
        reply_markup=back_markup
    )

    # Отправляем сообщение с миссией дефендеру
    if defender_id:
        try:
            defender_message = await build_mission_message(attacker_is_dominant, attacker_nickname, defender_lang)
            new_mission_prefix = await localization.get_text("new_mission_prefix", defender_lang)
            
            await context.bot.send_message(
                chat_id=defender_id, 
                text=f"{new_mission_prefix}\n{defender_message}"
            )
        except Exception as e:
            logger.error(
                f"Ошибка при отправке сообщения дефендеру {defender_id}: {e}")

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
    logger.info(f"🔧 back_to_main_menu called by user {userId}")

    query = update.callback_query
    logger.info(f"🔧 Callback data received: '{query.data}'")
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

    logger.info(f"🔧 Sending main menu to user {userId}")
    await query.edit_message_text(greeting_text, reply_markup=menu_markup)
    logger.info(f"🔧 Successfully returned to main menu for user {userId}")
    return MAIN_MENU


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userId = update.effective_user.id
    logger.info(f"hello function called by user {userId}")

    await players_helper.add_warmaster(userId)
    
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


async def show_alliance_resources(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display alliance resource amount for the user's alliance."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()

    alliance = await sqllite_helper.get_alliance_of_warmaster(user_id)
    alliance_id = alliance[0] if alliance else None

    if not alliance_id or alliance_id == 0:
        no_alliance_msg = await localization.get_text_for_user(user_id, "alliance_no_alliance")
        back_text = await localization.get_text_for_user(user_id, "button_back")
        await query.edit_message_text(
            no_alliance_msg,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(back_text, callback_data="back_to_main")]
            ])
        )
        return MAIN_MENU

    alliance_info = await sqllite_helper.get_alliance_by_id(alliance_id)
    alliance_name = alliance_info[1] if alliance_info else str(alliance_id)
    resources = await sqllite_helper.get_alliance_resources(alliance_id)

    info_text = await localization.get_text_for_user(
        user_id,
        "alliance_resources_message",
        alliance_name=alliance_name,
        resources=resources
    )
    back_text = await localization.get_text_for_user(user_id, "button_back")
    await query.edit_message_text(
        info_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(back_text, callback_data="back_to_main")]
        ])
    )
    return MAIN_MENU


async def appoint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userId = update.effective_user.id
    query = update.callback_query
    await query.answer()
    rules = await keyboard_constructor.get_keyboard_rules_keyboard_for_user(userId)
    menu = InlineKeyboardMarkup(rules)
    await query.edit_message_text(f'Choose the rules {update.effective_user.first_name}', reply_markup=menu)
    return GAMES


async def back_to_games(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle 'Back' button from day selection"""
    userId = update.effective_user.id
    logger.info(f"back_to_games called by user {userId}")

    query = update.callback_query
    await query.answer()

    rules = await keyboard_constructor.get_keyboard_rules_keyboard_for_user(userId)
    menu = InlineKeyboardMarkup(rules)
    await query.edit_message_text(f'Choose the rules {update.effective_user.first_name}', reply_markup=menu)
    logger.info("Successfully returned to games menu")
    return GAMES


async def im_in(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    data = query.data
    data_arr = data.split(',')
    # ['Sat Apr 27 00:00:00 2024', 'rule:killteam']

    game_date = data_arr[0]
    game_rules = data_arr[1].split(':')[1]
    user_id = update.effective_user.id

    # Check if user's alliance has territories
    alliance = await sqllite_helper.get_alliance_of_warmaster(user_id)
    
    if not alliance or alliance[0] is None or alliance[0] == 0:
        # User has no alliance
        error_message = await localization.get_text_for_user(user_id, "error_no_alliance")
        await query.answer()
        await query.edit_message_text(error_message)
        return MAIN_MENU
    
    # Check if alliance has territories
    territory_count = await sqllite_helper.get_alliance_territory_count(alliance[0])
    if territory_count == 0:
        # Alliance has no territories
        error_message = await localization.get_text_for_user(user_id, "error_no_territories")
        await query.answer()
        await query.edit_message_text(error_message)
        return MAIN_MENU

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
        no_signups_msg = await localization.get_text_for_user(user_id, "no_signups_today")
        await query.edit_message_text(no_signups_msg)
        alt_opponents = await players_helper.get_opponents_other_formats(user_id, data)
        if alt_opponents:
            message_lines = [
                'Ещё никто не запился на этот формат.',
                'Но на этот день будут игроки в другие форматы:'
            ]
            for opponent in alt_opponents:
                message_lines.append(f"- {opponent[0]} ({opponent[2]})")
            await query.edit_message_text('\n'.join(message_lines))
            for opponent in alt_opponents:
                if len(opponent) > 1 and opponent[1]:
                    await update.effective_chat.send_contact(
                        first_name=str(opponent[0]),
                        phone_number=opponent[1]
                    )
        else:
            no_signups_msg = await localization.get_text_for_user(user_id, "no_signups_today")
        await query.edit_message_text(no_signups_msg)
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
    await query.answer()
    user_id = update.effective_user.id
    # Callback data looks like "rule:wh40k" – strip the prefix for DB queries
    rule_key = query.data.split(':', 1)[1] if ':' in query.data else query.data
    when_markup = await keyboard_constructor.this_week(rule_key, user_id)
    menu = InlineKeyboardMarkup(when_markup)
    await query.edit_message_text(
        text=f"Selected option: {rule_key}", reply_markup=menu
    )
    return SCHEDULE


async def handle_mission_reply(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handler to process the reply to the message from show_missions.
    
    New flow:
    1. Player submits result by replying to mission message
    2. Result is stored as pending (not applied yet)
    3. Mission status set to 2 (pending confirmation)
    4. Other player receives confirmation request with buttons
    """
    # Retrieve the original message's text and user's reply
    original_message = (
        update.message.reply_to_message.text
        if update.message.reply_to_message else None
    )
    user_reply = update.message.text

    logger.info(
        "User %s replied with '%s' to original '%s'",
        update.effective_user.id, user_reply, original_message)

    if original_message is None:
        logger.error("Reply has no original message context (reply_to_message is None)")
        error_msg = await localization.get_text_for_user(update.effective_user.id, "error_score_format")
        await update.message.reply_text(error_msg)
        return MAIN_MENU

    # Validate score format
    try:
        counts = user_reply.split(' ')
        if len(counts) != 2:
            raise ValueError("Invalid format")
        submitter_score = int(counts[0])
        opponent_score = int(counts[1])
    except (ValueError, IndexError):
        error_msg = await localization.get_text_for_user(update.effective_user.id, "error_score_format")
        await update.message.reply_text(error_msg)
        return MAIN_MENU

    # Разделяем текст на строки
    lines = original_message.splitlines()

    # Ищем строку, начинающуюся с '#'
    mission_id_line = next(
        (line for line in lines if line.startswith('#')), None)
    if not mission_id_line:
        error_msg = await localization.get_text_for_user(update.effective_user.id, "error_mission_not_found")
        await update.message.reply_text(error_msg)
        return MAIN_MENU
        
    # Извлекаем значение после решётки - это реальный mission_id из базы
    mission_id = int(mission_id_line[1:])
    
    # Находим активный battle_id для этой миссии и пользователя
    battle_id = await sqllite_helper.get_active_battle_id_for_mission(
        mission_id, update.effective_user.id)
    
    if not battle_id:
        logger.error(f"No active battle found for mission {mission_id} and user {update.effective_user.id}")
        error_msg = await localization.get_text_for_user(update.effective_user.id, "error_no_active_battle")
        await update.message.reply_text(error_msg)
        return MAIN_MENU
    
    # Check if there's already a pending result for this battle
    existing_pending = await sqllite_helper.get_pending_result_by_battle_id(battle_id)
    if existing_pending:
        error_msg = await localization.get_text_for_user(update.effective_user.id, "error_already_submitted")
        await update.message.reply_text(error_msg)
        return MAIN_MENU
    
    logger.info(f"Found battle_id {battle_id} for mission_id {mission_id}")
    
    # Get battle participants
    participants = await sqllite_helper.get_battle_participants(battle_id)
    if not participants:
        error_msg = await localization.get_text_for_user(update.effective_user.id, "error_not_participant")
        await update.message.reply_text(error_msg)
        return MAIN_MENU
    
    fstplayer_id, sndplayer_id = participants
    submitter_id = str(update.effective_user.id)
    
    # Determine scores in database order (fstplayer, sndplayer)
    # User always enters their own score first, then opponent's score
    if submitter_id == fstplayer_id:
        fstplayer_score = submitter_score
        sndplayer_score = opponent_score
        opponent_id = sndplayer_id
    elif submitter_id == sndplayer_id:
        fstplayer_score = opponent_score
        sndplayer_score = submitter_score
        opponent_id = fstplayer_id
    else:
        error_msg = await localization.get_text_for_user(update.effective_user.id, "error_not_participant")
        await update.message.reply_text(error_msg)
        return MAIN_MENU
    
    # Create pending result
    pending_id = await sqllite_helper.create_pending_result(
        battle_id, submitter_id, fstplayer_score, sndplayer_score
    )
    
    if not pending_id:
        error_msg = await localization.get_text_for_user(update.effective_user.id, "error_saving_result")
        await update.message.reply_text(error_msg)
        return MAIN_MENU
    
    # Update mission status to 2 (pending confirmation)
    await sqllite_helper.update_mission_status(mission_id, 2)
    logger.info(f"Mission {mission_id} status set to 2 (pending confirmation)")
    
    # Get submitter and opponent nicknames
    submitter_nickname = await sqllite_helper.get_nickname_by_telegram_id(submitter_id)
    opponent_nickname = await sqllite_helper.get_nickname_by_telegram_id(opponent_id)
    
    # Get opponent's language for sending confirmation request
    opponent_lang = await localization.get_user_language(opponent_id)
    
    # Determine winner
    if submitter_score > opponent_score:
        winner_text = await localization.get_text(
            "winner_text", opponent_lang,
            winner=submitter_nickname,
            my_score=submitter_score,
            opponent_score=opponent_score
        )
    elif opponent_score > submitter_score:
        winner_text = await localization.get_text(
            "winner_text", opponent_lang,
            winner=opponent_nickname,
            my_score=submitter_score,
            opponent_score=opponent_score
        )
    else:
        winner_text = await localization.get_text(
            "draw_text", opponent_lang,
            my_score=submitter_score,
            opponent_score=opponent_score
        )
    
    # Send confirmation request to opponent
    btn_confirm_text = await localization.get_text("btn_confirm", opponent_lang)
    btn_reject_text = await localization.get_text("btn_reject", opponent_lang)
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(btn_confirm_text, callback_data=f"confirm_result_{battle_id}"),
            InlineKeyboardButton(btn_reject_text, callback_data=f"cancel_result_{battle_id}")
        ]
    ])
    
    confirmation_message = await localization.get_text(
        "result_confirm_question",
        opponent_lang,
        winner_text=winner_text,
        my_score=submitter_score,
        opponent_score=opponent_score
    )
    
    try:
        await context.bot.send_message(
            chat_id=opponent_id,
            text=confirmation_message,
            reply_markup=keyboard
        )
        logger.info(f"Sent confirmation request to {opponent_id} for battle {battle_id}")
    except Exception as e:
        logger.error(f"Failed to send confirmation request to {opponent_id}: {e}")
        # Still allow the flow to continue
    
    # Respond to submitter
    pending_msg = await localization.get_text_for_user(
        update.effective_user.id,
        "result_pending_confirmation",
        my_score=submitter_score,
        opponent_score=opponent_score
    )
    await update.message.reply_text(pending_msg)
    
    return MAIN_MENU


async def confirm_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for confirming a pending battle result."""
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    battle_id = int(query.data.replace("confirm_result_", ""))
    
    logger.info(f"User {user_id} confirming result for battle {battle_id}")
    
    # Get the pending result
    pending_result = await sqllite_helper.get_pending_result_by_battle_id(battle_id)
    if not pending_result:
        error_msg = await localization.get_text_for_user(user_id, "error_pending_not_found")
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    # Verify that the user is not the submitter
    if pending_result.submitter_id == user_id:
        error_msg = await localization.get_text_for_user(user_id, "error_no_permission_confirm")
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    # Get battle participants
    participants = await sqllite_helper.get_battle_participants(battle_id)
    if not participants:
        error_msg = await localization.get_text_for_user(user_id, "error_not_participant")
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    fstplayer_id, sndplayer_id = participants
    
    # Verify that the user is a participant
    if user_id not in [fstplayer_id, sndplayer_id]:
        error_msg = await localization.get_text_for_user(user_id, "error_not_participant")
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    # Get mission_id
    mission_id = await sqllite_helper.get_mission_id_for_battle(battle_id)
    if not mission_id:
        error_msg = await localization.get_text_for_user(user_id, "error_mission_not_found")
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    # Construct user_reply for existing functions
    user_reply = f"{pending_result.fstplayer_score} {pending_result.sndplayer_score}"
    
    try:
        # Apply the battle result using existing functions
        await mission_helper.write_battle_result(battle_id, user_reply)
        
        # Apply mission-specific rewards - use submitter_id as they originally entered the result
        rewards = await mission_helper.apply_mission_rewards(
            battle_id, user_reply, pending_result.submitter_id
        )
        
        if rewards is None:
            logger.warning(
                "Could not apply mission rewards for battle %s - "
                "check that both players are assigned to alliances",
                battle_id
            )
        
        # Update the map based on battle results
        # Get scenario from mission details if available
        mission_details = await sqllite_helper.get_mission_details(mission_id)
        scenario = mission_details.rules if mission_details else None
        
        await map_helper.update_map(
            battle_id,
            user_reply,
            pending_result.submitter_id,
            scenario
        )
        
        # Update mission status to 3 (confirmed)
        await sqllite_helper.update_mission_status(mission_id, 3)
        logger.info(f"Mission {mission_id} status set to 3 (confirmed)")
        
        # Delete the pending result
        await sqllite_helper.delete_pending_result(battle_id)
        
        # Get nicknames for message
        submitter_nickname = await sqllite_helper.get_nickname_by_telegram_id(pending_result.submitter_id)
        
        # Send success message
        success_msg = await localization.get_text_for_user(
            user_id,
            "result_confirmed",
            my_score=pending_result.fstplayer_score,
            opponent_score=pending_result.sndplayer_score
        )
        await query.edit_message_text(success_msg)
        
        # Notify the submitter that result was confirmed
        try:
            confirmer_nickname = await sqllite_helper.get_nickname_by_telegram_id(user_id)
            notification_msg = await localization.get_text_for_user(
                pending_result.submitter_id,
                "result_confirmed_notification",
                mission_id=mission_id,
                confirmer_name=confirmer_nickname,
                fst_score=pending_result.fstplayer_score,
                snd_score=pending_result.sndplayer_score
            )
            await context.bot.send_message(
                chat_id=pending_result.submitter_id,
                text=notification_msg
            )
        except Exception as e:
            logger.error(f"Failed to notify submitter {pending_result.submitter_id}: {e}")
        
    except Exception as e:
        logger.error(f"Error confirming result for battle {battle_id}: {e}", exc_info=True)
        error_msg = await localization.get_text_for_user(user_id, "error_result_application", error=str(e))
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    return MAIN_MENU


async def cancel_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for canceling a pending battle result."""
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    battle_id = int(query.data.replace("cancel_result_", ""))
    
    logger.info(f"User {user_id} canceling result for battle {battle_id}")
    
    # Get the pending result
    pending_result = await sqllite_helper.get_pending_result_by_battle_id(battle_id)
    if not pending_result:
        error_msg = await localization.get_text_for_user(user_id, "error_cancel_not_found")
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    # Verify that the user is not the submitter
    if pending_result.submitter_id == user_id:
        error_msg = await localization.get_text_for_user(user_id, "error_cannot_cancel_own")
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    # Get battle participants
    participants = await sqllite_helper.get_battle_participants(battle_id)
    if not participants:
        error_msg = await localization.get_text_for_user(user_id, "error_not_participant")
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    fstplayer_id, sndplayer_id = participants
    
    # Verify that the user is a participant
    if user_id not in [fstplayer_id, sndplayer_id]:
        error_msg = await localization.get_text_for_user(user_id, "error_not_participant")
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    # Get mission_id
    mission_id = await sqllite_helper.get_mission_id_for_battle(battle_id)
    if not mission_id:
        error_msg = await localization.get_text_for_user(user_id, "error_mission_not_found")
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    try:
        # Delete the pending result
        await sqllite_helper.delete_pending_result(battle_id)
        
        # Reset mission status to 1 (active) so they can resubmit
        await sqllite_helper.update_mission_status(mission_id, 1)
        logger.info(f"Mission {mission_id} status reset to 1 (active)")
        
        cancel_msg = await localization.get_text_for_user(user_id, "result_cancelled_success")
        await query.edit_message_text(cancel_msg)
        
        # Notify the submitter that result was canceled
        try:
            canceler_nickname = await sqllite_helper.get_nickname_by_telegram_id(user_id)
            notification_msg = await localization.get_text_for_user(
                pending_result.submitter_id,
                "result_cancelled_by_opponent",
                mission_id=mission_id,
                canceler_name=canceler_nickname
            )
            await context.bot.send_message(
                chat_id=pending_result.submitter_id,
                text=notification_msg
            )
        except Exception as e:
            logger.error(f"Failed to notify submitter {pending_result.submitter_id}: {e}")
        
    except Exception as e:
        logger.error(f"Error canceling result for battle {battle_id}: {e}", exc_info=True)
        error_msg = await localization.get_text_for_user(user_id, "error_cancellation_failed", error=str(e))
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    return MAIN_MENU


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
    
    name_prompt = await localization.get_text_for_user(user_id, "prompt_enter_name")
    await query.edit_message_text(
        f"{prompt_text}\n\n{name_prompt}",
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
    query = update.callback_query
    await query.answer()
    
    menu = await keyboard_constructor.today_schedule(user_id)
    markup = InlineKeyboardMarkup(menu)

    missions_text = await localization.get_text_for_user(user_id, "missions_title")
    await query.edit_message_text(missions_text, reply_markup=markup)
    return MISSIONS


async def back_to_missions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle 'Back' button from mission to return to missions list"""
    user_id = update.effective_user.id
    logger.info(f"back_to_missions called by user {user_id}")
    
    query = update.callback_query
    await query.answer()
    
    menu = await keyboard_constructor.today_schedule(user_id)
    markup = InlineKeyboardMarkup(menu)
    
    missions_text = await localization.get_text_for_user(user_id, "missions_title")
    await query.edit_message_text(missions_text, reply_markup=markup)
    logger.info(f"Successfully returned to missions list for user {user_id}")
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
    await sqllite_helper.set_warmaster_alliance(player_telegram_id, alliance_id)
    
    # Check and clean any empty alliances
    await sqllite_helper.check_and_clean_empty_alliances()
    
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


async def admin_appoint_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of users for admin to appoint as administrator."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    # Get keyboard with users
    menu = await keyboard_constructor.admin_appoint_admin_users(user_id)
    markup = InlineKeyboardMarkup(menu)
    
    admin_text = await localization.get_text_for_user(user_id, "admin_appoint_title")
    await query.edit_message_text(admin_text, reply_markup=markup)
    return MAIN_MENU


async def admin_make_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Admin appointed a user as administrator."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    # Extract user telegram ID from callback data
    target_user_telegram_id = query.data.split(':')[1]
    
    # Make user admin
    await sqllite_helper.make_user_admin(target_user_telegram_id)
    
    # Get user nickname for confirmation
    nickname = await sqllite_helper.get_nicknamane(target_user_telegram_id)
    
    # Show confirmation and return to main menu
    success_text = await localization.get_text_for_user(
        user_id, "admin_appointed_success", 
        user_name=nickname
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


# Alliance management handlers
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show admin menu with all admin options."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    logger.info(f"🔧 admin_menu called by user {user_id}")
    
    # Check if user is admin
    is_admin = await sqllite_helper.is_user_admin(user_id)
    logger.info(f"🔧 User {user_id} is_admin: {is_admin}")
    
    if not is_admin:
        logger.warning(f"🚫 Non-admin user {user_id} tried to access admin menu")
        error_text = await localization.get_text_for_user(user_id, "error_not_admin") or "У вас нет прав администратора"
        await query.edit_message_text(error_text)
        return MAIN_MENU
    
    menu = await keyboard_constructor.get_admin_menu(user_id)
    markup = InlineKeyboardMarkup(menu)
    
    admin_title = await localization.get_text_for_user(user_id, "admin_menu_title")
    logger.info(f"🔧 Showing admin menu to user {user_id} with title: {admin_title}")
    await query.edit_message_text(admin_title, reply_markup=markup)
    return MAIN_MENU


async def admin_adjust_resources_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of alliances for resource adjustments."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()

    is_admin = await sqllite_helper.is_user_admin(user_id)
    if not is_admin:
        error_text = await localization.get_text_for_user(user_id, "error_not_admin")
        await query.edit_message_text(error_text)
        return MAIN_MENU

    context.user_data.pop('resource_adjust_alliance_id', None)
    menu = await keyboard_constructor.get_alliance_list_for_resources(user_id)
    markup = InlineKeyboardMarkup(menu)
    title = await localization.get_text_for_user(user_id, "admin_adjust_resources_title")
    await query.edit_message_text(title, reply_markup=markup)
    return MAIN_MENU


async def admin_select_resource_alliance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompt admin to enter resource delta for selected alliance."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()

    is_admin = await sqllite_helper.is_user_admin(user_id)
    if not is_admin:
        error_text = await localization.get_text_for_user(user_id, "error_not_admin")
        await query.edit_message_text(error_text)
        return MAIN_MENU

    alliance_id = int(query.data.split(':')[1])
    context.user_data['resource_adjust_alliance_id'] = alliance_id

    alliance_info = await sqllite_helper.get_alliance_by_id(alliance_id)
    alliance_name = alliance_info[1] if alliance_info else str(alliance_id)
    current_resources = await sqllite_helper.get_alliance_resources(alliance_id)

    prompt_text = await localization.get_text_for_user(
        user_id,
        "admin_adjust_resource_prompt",
        alliance_name=alliance_name,
        current=current_resources
    )
    back_text = await localization.get_text_for_user(user_id, "button_back")
    await query.edit_message_text(
        prompt_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(back_text, callback_data="admin_adjust_resources")]
        ])
    )
    return ALLIANCE_INPUT


async def admin_alliance_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show alliance management menu."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    menu = await keyboard_constructor.get_alliance_management_menu(user_id)
    markup = InlineKeyboardMarkup(menu)
    
    title = await localization.get_text_for_user(user_id, "admin_alliance_management_title")
    await query.edit_message_text(title, reply_markup=markup)
    return MAIN_MENU


async def admin_create_alliance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start alliance creation process - prompt for name."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    # Ask for alliance name
    prompt_text = await localization.get_text_for_user(user_id, "admin_create_alliance_prompt")
    cancel_button = await localization.get_text_for_user(user_id, "button_cancel")
    
    cancel_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(cancel_button, callback_data="admin_alliance_management")]
    ])
    
    await query.edit_message_text(prompt_text, reply_markup=cancel_markup)
    return ALLIANCE_INPUT


async def handle_alliance_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle alliance name input and create alliance."""
    user_id = update.effective_user.id
    alliance_name = update.message.text.strip()
    
    try:
        # Create alliance
        alliance_id = await sqllite_helper.create_alliance(alliance_name)
        
        if alliance_id:
            # Success
            success_text = await localization.get_text_for_user(
                user_id, "admin_alliance_created_success", alliance_name=alliance_name
            )
        else:
            # Name already exists
            success_text = await localization.get_text_for_user(
                user_id, "admin_alliance_name_exists", alliance_name=alliance_name
            )
        
    except ValueError as e:
        # Validation error
        error_text = await localization.get_text_for_user(user_id, "admin_alliance_creation_error")
        success_text = f"{error_text}\n{str(e)}"
    
    # Return to alliance management menu
    menu = await keyboard_constructor.get_alliance_management_menu(user_id)
    markup = InlineKeyboardMarkup(menu)
    
    await update.message.reply_text(success_text, reply_markup=markup)
    return MAIN_MENU


async def admin_edit_alliances(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of alliances for editing."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    menu = await keyboard_constructor.get_alliance_list_for_edit(user_id)
    markup = InlineKeyboardMarkup(menu)
    
    title = await localization.get_text_for_user(user_id, "admin_edit_alliances_title")
    await query.edit_message_text(title, reply_markup=markup)
    return MAIN_MENU


async def admin_edit_alliance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show options for editing specific alliance."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    # Extract alliance ID
    alliance_id = int(query.data.split(':')[1])
    
    # Get alliance info
    alliance = await sqllite_helper.get_alliance_by_id(alliance_id)
    if not alliance:
        error_text = await localization.get_text_for_user(user_id, "admin_alliance_not_found")
        await query.edit_message_text(error_text)
        return MAIN_MENU
    
    alliance_name = alliance[1]
    
    # Show edit options
    menu = await keyboard_constructor.get_alliance_confirmation_keyboard(
        user_id, "edit", alliance_id, alliance_name
    )
    markup = InlineKeyboardMarkup(menu)
    
    edit_text = await localization.get_text_for_user(
        user_id, "admin_edit_alliance_title", alliance_name=alliance_name
    )
    await query.edit_message_text(edit_text, reply_markup=markup)
    return MAIN_MENU


async def admin_rename_alliance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start alliance renaming process - prompt for new name."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    # Extract alliance ID and store in context
    alliance_id = int(query.data.split(':')[1])
    context.user_data['renaming_alliance_id'] = alliance_id
    
    # Get current alliance name
    alliance = await sqllite_helper.get_alliance_by_id(alliance_id)
    alliance_name = alliance[1] if alliance else "Unknown"
    
    # Ask for new name
    prompt_text = await localization.get_text_for_user(
        user_id, "admin_rename_alliance_prompt", alliance_name=alliance_name
    )
    cancel_button = await localization.get_text_for_user(user_id, "button_cancel")
    
    cancel_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(cancel_button, callback_data="admin_edit_alliances")]
    ])
    
    await query.edit_message_text(prompt_text, reply_markup=cancel_markup)
    return ALLIANCE_INPUT


async def handle_alliance_rename_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle alliance rename input."""
    user_id = update.effective_user.id
    new_name = update.message.text.strip()
    alliance_id = context.user_data.get('renaming_alliance_id')
    
    if not alliance_id:
        error_text = await localization.get_text_for_user(user_id, "admin_alliance_rename_error")
        await update.message.reply_text(error_text)
        return MAIN_MENU
    
    try:
        # Update alliance name
        success = await sqllite_helper.update_alliance_name(alliance_id, new_name)
        
        if success:
            success_text = await localization.get_text_for_user(
                user_id, "admin_alliance_renamed_success", alliance_name=new_name
            )
        else:
            success_text = await localization.get_text_for_user(
                user_id, "admin_alliance_name_exists", alliance_name=new_name
            )
        
    except ValueError as e:
        error_text = await localization.get_text_for_user(user_id, "admin_alliance_rename_error")
        success_text = f"{error_text}\n{str(e)}"
    
    # Clean up context
    context.user_data.pop('renaming_alliance_id', None)
    
    # Return to edit menu
    menu = await keyboard_constructor.get_alliance_list_for_edit(user_id)
    markup = InlineKeyboardMarkup(menu)
    
    await update.message.reply_text(success_text, reply_markup=markup)
    return MAIN_MENU


async def admin_delete_alliances(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of alliances for deletion."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    menu = await keyboard_constructor.get_alliance_list_for_delete(user_id)
    markup = InlineKeyboardMarkup(menu)
    
    title = await localization.get_text_for_user(user_id, "admin_delete_alliances_title")
    await query.edit_message_text(title, reply_markup=markup)
    return MAIN_MENU


async def admin_delete_alliance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show confirmation for alliance deletion."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    # Extract alliance ID
    alliance_id = int(query.data.split(':')[1])
    
    # Get alliance info
    alliance = await sqllite_helper.get_alliance_by_id(alliance_id)
    if not alliance:
        error_text = await localization.get_text_for_user(user_id, "admin_alliance_not_found")
        await query.edit_message_text(error_text)
        return MAIN_MENU
    
    alliance_name = alliance[1]
    player_count = await sqllite_helper.get_alliance_player_count(alliance_id)
    
    # Show confirmation
    menu = await keyboard_constructor.get_alliance_confirmation_keyboard(
        user_id, "delete", alliance_id, alliance_name
    )
    markup = InlineKeyboardMarkup(menu)
    
    confirm_text = await localization.get_text_for_user(
        user_id, "admin_delete_alliance_confirm", 
        alliance_name=alliance_name, player_count=player_count
    )
    await query.edit_message_text(confirm_text, reply_markup=markup)
    return MAIN_MENU


async def admin_confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and execute alliance deletion."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    # Extract alliance ID
    alliance_id = int(query.data.split(':')[1])
    
    # Delete alliance
    result = await sqllite_helper.delete_alliance(alliance_id)
    
    if result['success']:
        success_text = await localization.get_text_for_user(
            user_id, "admin_alliance_deleted_success",
            alliance_name=result.get('message', 'Unknown'),
            players_redistributed=result['players_redistributed'],
            territories_redistributed=result['territories_redistributed']
        )
    else:
        error_text = await localization.get_text_for_user(user_id, "admin_alliance_deletion_error")
        success_text = f"{error_text}\n{result['message']}"
    
    # Return to alliance management
    menu = await keyboard_constructor.get_alliance_management_menu(user_id)
    markup = InlineKeyboardMarkup(menu)
    
    await query.edit_message_text(success_text, reply_markup=markup)
    return MAIN_MENU


async def handle_alliance_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Route text input to appropriate alliance handler based on context."""
    user_id = update.effective_user.id

    if 'resource_adjust_alliance_id' in context.user_data:
        alliance_id = context.user_data['resource_adjust_alliance_id']
        try:
            delta = int(update.message.text.strip())
        except ValueError:
            error_text = await localization.get_text_for_user(user_id, "admin_adjust_resource_invalid")
            await update.message.reply_text(error_text)
            return ALLIANCE_INPUT

        if delta >= 0:
            new_value = await sqllite_helper.increase_common_resource(alliance_id, delta)
        else:
            new_value = await sqllite_helper.decrease_common_resource(alliance_id, abs(delta))

        alliance_info = await sqllite_helper.get_alliance_by_id(alliance_id)
        alliance_name = alliance_info[1] if alliance_info else str(alliance_id)
        success_text = await localization.get_text_for_user(
            user_id,
            "admin_adjust_resource_success",
            alliance_name=alliance_name,
            delta=delta,
            new_value=new_value
        )

        context.user_data.pop('resource_adjust_alliance_id', None)
        menu = await keyboard_constructor.get_admin_menu(user_id)
        markup = InlineKeyboardMarkup(menu)

        await update.message.reply_text(success_text, reply_markup=markup)
        return MAIN_MENU

    # Check if we're in a renaming operation
    if 'renaming_alliance_id' in context.user_data:
        return await handle_alliance_rename_input(update, context)
    else:
        # Assume we're creating a new alliance
        return await handle_alliance_name_input(update, context)


async def admin_pending_confirmations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of missions pending confirmation."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    # Check if user is admin
    is_admin = await sqllite_helper.is_user_admin(user_id)
    if not is_admin:
        error_msg = await localization.get_text_for_user(user_id, "error_no_admin_rights")
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    # Get all pending missions
    pending_missions = await sqllite_helper.get_all_pending_missions()
    
    if not pending_missions:
        no_pending_msg = await localization.get_text_for_user(user_id, "admin_no_pending_missions")
        btn_back_text = await localization.get_text_for_user(user_id, "btn_back")
        await query.edit_message_text(
            no_pending_msg,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(btn_back_text, callback_data="admin_menu")
            ]])
        )
        return MAIN_MENU
    
    # Build keyboard with pending missions
    keyboard = []
    for mission in pending_missions:
        mission_id, deploy, rules, cell, description, created_date = mission
        
        # Get pending result for this mission
        # Find battle_id for this mission
        battle_id = await sqllite_helper.get_battle_id_by_mission_id(mission_id)
        if battle_id:
            pending = await sqllite_helper.get_pending_result_by_battle_id(battle_id)
            if pending:
                score_text = f"{pending.fstplayer_score}:{pending.sndplayer_score}"
            else:
                score_text = "?"
        else:
            score_text = "?"
        
        button_text = f"#{mission_id} - {rules} ({score_text})"
        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"admin_confirm_mission:{mission_id}"
            )
        ])
    
    btn_back_admin_text = await localization.get_text_for_user(user_id, "btn_back_admin_menu")
    keyboard.append([
        InlineKeyboardButton(btn_back_admin_text, callback_data="admin_menu")
    ])
    
    markup = InlineKeyboardMarkup(keyboard)
    pending_title = await localization.get_text_for_user(
        user_id,
        "admin_pending_missions_title",
        count=len(pending_missions)
    )
    await query.edit_message_text(
        pending_title,
        reply_markup=markup
    )
    return MAIN_MENU


async def admin_confirm_mission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Admin confirms a specific pending mission."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    # Check if user is admin
    is_admin = await sqllite_helper.is_user_admin(user_id)
    if not is_admin:
        error_msg = await localization.get_text_for_user(user_id, "error_no_admin_rights")
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    # Extract mission_id from callback data
    mission_id = int(query.data.split(':')[1])
    
    # Get battle_id for this mission
    battle_id = await sqllite_helper.get_battle_id_by_mission_id(mission_id)
    if not battle_id:
        error_msg = await localization.get_text_for_user(user_id, "admin_battle_not_found", mission_id=mission_id)
        btn_back_text = await localization.get_text_for_user(user_id, "btn_back")
        await query.edit_message_text(
            error_msg,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(btn_back_text, callback_data="admin_pending_confirmations")
            ]])
        )
        return MAIN_MENU
    
    # Get pending result
    pending_result = await sqllite_helper.get_pending_result_by_battle_id(battle_id)
    if not pending_result:
        error_msg = await localization.get_text_for_user(user_id, "admin_pending_not_found", mission_id=mission_id)
        btn_back_text = await localization.get_text_for_user(user_id, "btn_back")
        await query.edit_message_text(
            error_msg,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(btn_back_text, callback_data="admin_pending_confirmations")
            ]])
        )
        return MAIN_MENU
    
    # Get mission details
    mission_details = await sqllite_helper.get_mission_details(mission_id)
    if not mission_details:
        error_msg = await localization.get_text_for_user(user_id, "error_mission_not_found")
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    # Get participant names
    participants = await sqllite_helper.get_battle_participants(battle_id)
    if participants:
        fstplayer_id, sndplayer_id = participants
        fstplayer_name = await sqllite_helper.get_nickname_by_telegram_id(fstplayer_id)
        sndplayer_name = await sqllite_helper.get_nickname_by_telegram_id(sndplayer_id)
        submitter_name = await sqllite_helper.get_nickname_by_telegram_id(pending_result.submitter_id)
        
        participants_label = await localization.get_text_for_user(user_id, "admin_participants_label")
        result_label = await localization.get_text_for_user(user_id, "admin_result_submitted_label")
        participants_text = (
            f"{participants_label}\n"
            f"  • {fstplayer_name} ({pending_result.fstplayer_score})\n"
            f"  • {sndplayer_name} ({pending_result.sndplayer_score})\n"
            f"{result_label} {submitter_name}\n"
        )
    else:
        participants_label = await localization.get_text_for_user(user_id, "admin_participants_label")
        participants_text = f"{participants_label} неизвестны\n"
    
    # Determine winner
    if pending_result.fstplayer_score > pending_result.sndplayer_score:
        winner_text = await localization.get_text_for_user(user_id, "admin_winner_text", winner=fstplayer_name)
    elif pending_result.sndplayer_score > pending_result.fstplayer_score:
        winner_text = await localization.get_text_for_user(user_id, "admin_winner_text", winner=sndplayer_name)
    else:
        winner_text = await localization.get_text_for_user(user_id, "admin_draw_text")
    
    confirm_question = await localization.get_text_for_user(user_id, "admin_confirm_question")
    message_text = await localization.get_text_for_user(
        user_id,
        "admin_mission_details",
        mission_id=mission_id,
        created_date=mission_details.created_date if mission_details else 'неизвестно',
        rules=mission_details.rules if mission_details else 'неизвестно',
        participants=participants_text,
        submitter=submitter_name if participants else 'неизвестно',
        fst_score=pending_result.fstplayer_score,
        snd_score=pending_result.sndplayer_score,
        winner_text=winner_text
    ) + f"\n\n{confirm_question}"
    
    btn_confirm_text = await localization.get_text_for_user(user_id, "btn_confirm")
    btn_reject_text = await localization.get_text_for_user(user_id, "btn_reject")
    keyboard = [
        [
            InlineKeyboardButton(btn_confirm_text, callback_data=f"admin_do_confirm:{battle_id}"),
            InlineKeyboardButton(btn_reject_text, callback_data=f"admin_do_reject:{battle_id}")
        ],
        [
            InlineKeyboardButton(await localization.get_text_for_user(user_id, "btn_back"), callback_data="admin_pending_confirmations")
        ]
    ]
    
    await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(keyboard))
    return MAIN_MENU


async def admin_do_confirm_mission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Admin actually confirms the mission result."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    # Check if user is admin
    is_admin = await sqllite_helper.is_user_admin(user_id)
    if not is_admin:
        error_msg = await localization.get_text_for_user(user_id, "error_no_admin_rights")
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    # Extract battle_id from callback data
    battle_id = int(query.data.split(':')[1])
    
    # Get pending result
    pending_result = await sqllite_helper.get_pending_result_by_battle_id(battle_id)
    if not pending_result:
        error_msg = await localization.get_text_for_user(user_id, "error_pending_not_found")
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    # Get mission_id
    mission_id = await sqllite_helper.get_mission_id_for_battle(battle_id)
    if not mission_id:
        error_msg = await localization.get_text_for_user(user_id, "error_mission_not_found")
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    # Construct user_reply for existing functions
    user_reply = f"{pending_result.fstplayer_score} {pending_result.sndplayer_score}"
    
    try:
        # Apply the battle result
        await mission_helper.write_battle_result(battle_id, user_reply)
        
        # Apply mission-specific rewards
        rewards = await mission_helper.apply_mission_rewards(
            battle_id, user_reply, pending_result.submitter_id
        )
        
        if rewards is None:
            logger.warning(
                "Could not apply mission rewards for battle %s - "
                "check that both players are assigned to alliances",
                battle_id
            )
        
        # Update the map
        mission_details = await sqllite_helper.get_mission_details(mission_id)
        scenario = mission_details.rules if mission_details else None
        
        await map_helper.update_map(
            battle_id,
            user_reply,
            pending_result.submitter_id,
            scenario
        )
        
        # Update mission status to 3 (confirmed)
        await sqllite_helper.update_mission_status(mission_id, 3)
        logger.info(f"Admin confirmed mission {mission_id}, status set to 3")
        
        # Delete the pending result
        await sqllite_helper.delete_pending_result(battle_id)
        
        # Notify participants
        participants = await sqllite_helper.get_battle_participants(battle_id)
        if participants:
            for participant_id in participants:
                try:
                    notification_msg = await localization.get_text_for_user(
                        participant_id,
                        "admin_confirmed_by_admin",
                        mission_id=mission_id,
                        fst_score=pending_result.fstplayer_score,
                        snd_score=pending_result.sndplayer_score
                    )
                    await context.bot.send_message(
                        chat_id=participant_id,
                        text=notification_msg
                    )
                except Exception as e:
                    logger.error(f"Failed to notify participant {participant_id}: {e}")
        
        success_msg = await localization.get_text_for_user(
            user_id,
            "admin_confirm_result_success",
            mission_id=mission_id,
            fst_score=pending_result.fstplayer_score,
            snd_score=pending_result.sndplayer_score
        )
        btn_back_text = await localization.get_text_for_user(user_id, "btn_back")
        await query.edit_message_text(
            success_msg,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(btn_back_text, callback_data="admin_pending_confirmations")
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error confirming mission {mission_id}: {e}", exc_info=True)
        error_msg = await localization.get_text_for_user(user_id, "error_confirm_failed", error=str(e))
        await query.edit_message_text(error_msg)
    
    return MAIN_MENU


async def admin_do_reject_mission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Admin rejects a pending mission result."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    # Check if user is admin
    is_admin = await sqllite_helper.is_user_admin(user_id)
    if not is_admin:
        error_msg = await localization.get_text_for_user(user_id, "error_no_admin_rights")
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    # Extract battle_id from callback data
    battle_id = int(query.data.split(':')[1])
    
    # Get pending result
    pending_result = await sqllite_helper.get_pending_result_by_battle_id(battle_id)
    if not pending_result:
        error_msg = await localization.get_text_for_user(user_id, "error_pending_not_found")
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    # Get mission_id
    mission_id = await sqllite_helper.get_mission_id_for_battle(battle_id)
    if not mission_id:
        error_msg = await localization.get_text_for_user(user_id, "error_mission_not_found")
        await query.edit_message_text(error_msg)
        return MAIN_MENU
    
    try:
        # Delete the pending result
        await sqllite_helper.delete_pending_result(battle_id)
        
        # Reset mission status to 1 (active)
        await sqllite_helper.update_mission_status(mission_id, 1)
        logger.info(f"Admin rejected mission {mission_id}, status reset to 1")
        
        # Notify participants
        participants = await sqllite_helper.get_battle_participants(battle_id)
        if participants:
            for participant_id in participants:
                try:
                    notification_msg = await localization.get_text_for_user(
                        participant_id,
                        "admin_rejected_by_admin",
                        mission_id=mission_id
                    )
                    await context.bot.send_message(
                        chat_id=participant_id,
                        text=notification_msg
                    )
                except Exception as e:
                    logger.error(f"Failed to notify participant {participant_id}: {e}")
        
        success_msg = await localization.get_text_for_user(
            user_id,
            "admin_reject_result_success",
            mission_id=mission_id
        )
        btn_back_text = await localization.get_text_for_user(user_id, "btn_back")
        await query.edit_message_text(
            success_msg,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(btn_back_text, callback_data="admin_pending_confirmations")
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error rejecting mission {mission_id}: {e}", exc_info=True)
        error_msg = await localization.get_text_for_user(user_id, "error_reject_failed", error=str(e))
        await query.edit_message_text(error_msg)
    
    return MAIN_MENU


async def debug_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug handler for unmatched callbacks"""
    query = update.callback_query
    user_id = update.effective_user.id
    logger.warning(f"Unmatched callback from user {user_id}: '{query.data}' in current state")
    logger.warning(f"Current conversation state: {context.user_data}")
    await query.answer(f"Debug: Callback '{query.data}' not handled")
    return ConversationHandler.END


# ============================================================================
# Custom Notification Handlers
# ============================================================================

async def admin_custom_notification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start custom notification process - select recipient type."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    # Check if user is admin
    is_admin = await sqllite_helper.is_user_admin(user_id)
    if not is_admin:
        error_text = await localization.get_text_for_user(user_id, "error_not_admin")
        await query.edit_message_text(error_text)
        return MAIN_MENU
    
    # Show recipient type selection menu
    menu_text = await localization.get_text_for_user(user_id, "custom_notification_select_recipient_type")
    
    keyboard = [
        [InlineKeyboardButton(
            await localization.get_text_for_user(user_id, "button_notify_warmaster"),
            callback_data="notify_type_warmaster")],
        [InlineKeyboardButton(
            await localization.get_text_for_user(user_id, "button_notify_alliance"),
            callback_data="notify_type_alliance")],
        [InlineKeyboardButton(
            await localization.get_text_for_user(user_id, "button_back"),
            callback_data="admin_menu")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(menu_text, reply_markup=markup)
    return MAIN_MENU


async def admin_select_notification_warmaster(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of warmasters to select recipient."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    # Get all warmasters with nicknames
    warmasters = await sqllite_helper.get_warmasters_with_nicknames()
    
    if not warmasters:
        error_text = await localization.get_text_for_user(user_id, "no_warmasters_found")
        back_button = await localization.get_text_for_user(user_id, "button_back")
        keyboard = [[InlineKeyboardButton(back_button, callback_data="admin_custom_notification")]]
        await query.edit_message_text(error_text, reply_markup=InlineKeyboardMarkup(keyboard))
        return MAIN_MENU
    
    menu_text = await localization.get_text_for_user(user_id, "custom_notification_select_warmaster")
    
    keyboard = []
    for warmaster in warmasters:
        telegram_id = warmaster[0]
        nickname = warmaster[1]
        keyboard.append([InlineKeyboardButton(
            nickname,
            callback_data=f"notify_warmaster:{telegram_id}")])
    
    # Add back button
    back_button = await localization.get_text_for_user(user_id, "button_back")
    keyboard.append([InlineKeyboardButton(back_button, callback_data="admin_custom_notification")])
    
    markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(menu_text, reply_markup=markup)
    return MAIN_MENU


async def admin_select_notification_alliance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of alliances to select recipients."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    # Get all alliances
    alliances = await sqllite_helper.get_all_alliances()
    
    if not alliances:
        error_text = await localization.get_text_for_user(user_id, "no_alliances_found")
        back_button = await localization.get_text_for_user(user_id, "button_back")
        keyboard = [[InlineKeyboardButton(back_button, callback_data="admin_custom_notification")]]
        await query.edit_message_text(error_text, reply_markup=InlineKeyboardMarkup(keyboard))
        return MAIN_MENU
    
    menu_text = await localization.get_text_for_user(user_id, "custom_notification_select_alliance")
    
    keyboard = []
    for alliance in alliances:
        alliance_id = alliance[0]
        alliance_name = alliance[1]
        keyboard.append([InlineKeyboardButton(
            alliance_name,
            callback_data=f"notify_alliance:{alliance_id}")])
    
    # Add back button
    back_button = await localization.get_text_for_user(user_id, "button_back")
    keyboard.append([InlineKeyboardButton(back_button, callback_data="admin_custom_notification")])
    
    markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(menu_text, reply_markup=markup)
    return MAIN_MENU


async def admin_request_notification_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Request the admin to send the message content."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    # Parse recipient info from callback data
    if callback_data.startswith("notify_warmaster:"):
        recipient_id = callback_data.replace("notify_warmaster:", "")
        context.user_data['notification_type'] = 'warmaster'
        context.user_data['notification_recipient'] = recipient_id
        
        # Get warmaster nickname for confirmation
        warmaster = await sqllite_helper.get_settings(recipient_id)
        recipient_name = warmaster[0] if warmaster else recipient_id
        
    elif callback_data.startswith("notify_alliance:"):
        alliance_id = int(callback_data.replace("notify_alliance:", ""))
        context.user_data['notification_type'] = 'alliance'
        context.user_data['notification_recipient'] = alliance_id
        
        # Get alliance name for confirmation
        alliances = await sqllite_helper.get_all_alliances()
        recipient_name = next((a[1] for a in alliances if a[0] == alliance_id), str(alliance_id))
    else:
        return MAIN_MENU
    
    # Show instructions to admin
    instruction_text = await localization.get_text_for_user(
        user_id, 
        "custom_notification_send_message",
        recipient_name=recipient_name
    )
    
    # Add cancel button
    cancel_button = await localization.get_text_for_user(user_id, "button_cancel")
    keyboard = [[InlineKeyboardButton(cancel_button, callback_data="admin_menu")]]
    markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(instruction_text, reply_markup=markup)
    return CUSTOM_NOTIFICATION


async def handle_notification_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the message that admin wants to send to recipients."""
    user_id = update.effective_user.id
    
    # Check if user is admin
    is_admin = await sqllite_helper.is_user_admin(user_id)
    if not is_admin:
        return MAIN_MENU
    
    # Check if we have recipient info
    if 'notification_type' not in context.user_data or 'notification_recipient' not in context.user_data:
        error_text = await localization.get_text_for_user(user_id, "error_notification_session_expired")
        await update.message.reply_text(error_text)
        return MAIN_MENU
    
    notification_type = context.user_data['notification_type']
    recipient = context.user_data['notification_recipient']
    
    # Determine recipients list
    recipients = []
    if notification_type == 'warmaster':
        recipients = [recipient]
        warmaster_settings = await sqllite_helper.get_settings(recipient)
        recipient_description = warmaster_settings[0] if warmaster_settings else recipient
    elif notification_type == 'alliance':
        alliance_players = await sqllite_helper.get_players_by_alliance(recipient)
        recipients = [player[0] for player in alliance_players]
        alliances = await sqllite_helper.get_all_alliances()
        recipient_description = next((a[1] for a in alliances if a[0] == recipient), str(recipient))
    
    if not recipients:
        error_text = await localization.get_text_for_user(user_id, "error_no_recipients")
        await update.message.reply_text(error_text)
        return MAIN_MENU
    
    # Send the message to all recipients
    success_count = 0
    failure_count = 0
    
    for recipient_id in recipients:
        try:
            # Check if message has photo
            if update.message.photo:
                # Get the largest photo
                photo = update.message.photo[-1]
                caption = update.message.caption if update.message.caption else ""
                
                await context.bot.send_photo(
                    chat_id=recipient_id,
                    photo=photo.file_id,
                    caption=caption
                )
            elif update.message.text:
                # Send text message
                await context.bot.send_message(
                    chat_id=recipient_id,
                    text=update.message.text
                )
            else:
                # Unsupported message type
                continue
                
            success_count += 1
            logger.info(f"Custom notification sent to {recipient_id}")
            
        except Exception as e:
            failure_count += 1
            logger.error(f"Failed to send custom notification to {recipient_id}: {e}")
    
    # Send confirmation to admin
    confirmation_text = await localization.get_text_for_user(
        user_id,
        "custom_notification_sent",
        recipient_name=recipient_description,
        success_count=success_count,
        failure_count=failure_count
    )
    
    # Return to main menu
    menu = await keyboard_constructor.main_menu(user_id)
    markup = InlineKeyboardMarkup(menu)
    
    await update.message.reply_text(confirmation_text, reply_markup=markup)
    
    # Clear user data
    context.user_data.pop('notification_type', None)
    context.user_data.pop('notification_recipient', None)
    
    return MAIN_MENU


def start_bot():
    """Initialize and start the Telegram bot."""
    # Run database migrations before starting the bot
    print("🔄 Checking for pending database migrations...")
    migration_success = migrate_db.run_migrations()
    if not migration_success:
        print("❌ Database migration failed! Bot cannot start.")
        return False
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
                CallbackQueryHandler(show_alliance_resources, pattern='^alliance_resources$'),
                CallbackQueryHandler(registration_call, pattern='^registration$'),
                CallbackQueryHandler(show_missions, pattern='^callmissions$'),
                CallbackQueryHandler(change_language, pattern='^changelanguage$'),
                CallbackQueryHandler(set_language, pattern='^lang:'),
                CallbackQueryHandler(toggle_notifications,
                                     pattern='^togglenotifications$'),
                CallbackQueryHandler(
                    back_to_settings, pattern='^back_to_settings$'),
                # Admin handlers
                CallbackQueryHandler(admin_menu, pattern='^admin_menu$'),
                CallbackQueryHandler(admin_assign_alliance, pattern='^admin_assign_alliance$'),
                CallbackQueryHandler(admin_select_player, pattern='^admin_player:'),
                CallbackQueryHandler(admin_assign_alliance_to_player, pattern='^admin_alliance:'),
                CallbackQueryHandler(admin_appoint_admin, pattern='^admin_appoint_admin$'),
                CallbackQueryHandler(admin_make_user_admin, pattern='^admin_make_admin:'),
                CallbackQueryHandler(admin_adjust_resources_menu, pattern='^admin_adjust_resources$'),
                CallbackQueryHandler(admin_select_resource_alliance, pattern='^admin_adjust_alliance:'),
                # Alliance management handlers
                CallbackQueryHandler(admin_alliance_management, pattern='^admin_alliance_management$'),
                CallbackQueryHandler(admin_create_alliance, pattern='^admin_create_alliance$'),
                CallbackQueryHandler(admin_edit_alliances, pattern='^admin_edit_alliances$'),
                CallbackQueryHandler(admin_edit_alliance, pattern='^admin_edit_alliance:'),
                CallbackQueryHandler(admin_rename_alliance, pattern='^admin_rename_alliance:'),
                CallbackQueryHandler(admin_delete_alliances, pattern='^admin_delete_alliances$'),
                CallbackQueryHandler(admin_delete_alliance, pattern='^admin_delete_alliance:'),
                CallbackQueryHandler(admin_confirm_delete, pattern='^admin_confirm_delete:'),
                # Pending confirmations handlers
                CallbackQueryHandler(admin_pending_confirmations, pattern='^admin_pending_confirmations$'),
                CallbackQueryHandler(admin_confirm_mission, pattern='^admin_confirm_mission:'),
                CallbackQueryHandler(admin_do_confirm_mission, pattern='^admin_do_confirm:'),
                CallbackQueryHandler(admin_do_reject_mission, pattern='^admin_do_reject:'),
                # Custom notification handlers
                CallbackQueryHandler(admin_custom_notification, pattern='^admin_custom_notification$'),
                CallbackQueryHandler(admin_select_notification_warmaster, pattern='^notify_type_warmaster$'),
                CallbackQueryHandler(admin_select_notification_alliance, pattern='^notify_type_alliance$'),
                CallbackQueryHandler(admin_request_notification_message, pattern='^notify_warmaster:'),
                CallbackQueryHandler(admin_request_notification_message, pattern='^notify_alliance:'),
                # Result confirmation handlers
                CallbackQueryHandler(confirm_result, pattern='^confirm_result_'),
                CallbackQueryHandler(cancel_result, pattern='^cancel_result_'),
                # Back to main menu handler
                CallbackQueryHandler(back_to_main_menu, pattern='^back_to_main$')
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
                CallbackQueryHandler(back_to_games, pattern='^back_to_games$'),
                # Matches date,rule:rulename format
                CallbackQueryHandler(im_in, pattern=r'^.+,rule:.+$')
            ],
            MISSIONS: [
                CallbackQueryHandler(hello, pattern='^start$'),
                CallbackQueryHandler(back_to_missions, pattern='^back_to_missions$'),
                CallbackQueryHandler(get_the_mission, pattern='^mission_sch_')
            ],
            ALLIANCE_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_alliance_text_input),
                CallbackQueryHandler(admin_alliance_management, pattern='^admin_alliance_management$'),
                CallbackQueryHandler(admin_adjust_resources_menu, pattern='^admin_adjust_resources$')
                CallbackQueryHandler(admin_edit_alliances, pattern='^admin_edit_alliances$')
            ],
            CUSTOM_NOTIFICATION: [
                MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, handle_notification_message),
                CallbackQueryHandler(admin_menu, pattern='^admin_menu$')
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

    print("🤖 Starting Telegram bot polling...")
    bot.run_polling()
    return True


# Auto-start bot if this file is run directly (for backwards compatibility)
if __name__ == "__main__":
    start_bot()
