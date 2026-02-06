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

MAIN_MENU, SETTINGS, GAMES, SCHEDULE, MISSIONS, ALLIANCE_INPUT = range(6)
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
        await query.edit_message_text("❌ Ошибка: неверный формат запроса. Пожалуйста, попробуйте снова.")
        return MISSIONS
    
    try:
        # Parse callback data: mission_sch_{schedule_id}_{opponent_telegram_id}
        data_parts = query.data.replace("mission_sch_", "").split("_")
        mission_number = int(data_parts[0])
        defender_id = str(data_parts[1])  # Opponent telegram_id from callback
    except (ValueError, AttributeError, IndexError) as e:
        logger.error(f"Failed to parse mission callback data '{query.data}': {e}")
        await query.edit_message_text("❌ Ошибка: не удалось получить информацию о миссии. Пожалуйста, попробуйте снова.")
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
        await query.edit_message_text("Ошибка: не удалось найти противника для битвы")
        return MISSIONS
    
    try:
        battle_id = await mission_helper.start_battle(mission_id, attacker_id, defender_id)
    except ValueError as e:
        logger.error(f"Failed to start battle: {e}")
        await query.edit_message_text(f"Ошибка при создании битвы: {str(e)}")
        return MISSIONS
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
    
    # Helper function to build message for a player
    def build_mission_message(opponent_is_dominant, opponent_nickname):
        builder = mission_message_builder.MissionMessageBuilder(
            mission_id, mission_description, mission_rules
        )
        
        # Add double exp bonus if opponent is dominant
        if opponent_is_dominant:
            builder.add_double_exp_bonus(opponent_nickname)
        
        # Add common components
        builder.add_situation(situation)
        builder.add_reinforcement_message(reinforcement_message)
        
        return builder.build()
    
    # Build messages for both players
    attacker_message = build_mission_message(defender_is_dominant, defender_nickname)
    logger.info(f"Composed mission text for attacker: {attacker_message}")

    # Отправляем текст миссии текущему пользователю (атакующему)
    # Create Back button to return to missions list
    back_button = [[InlineKeyboardButton("⬅️ Назад к миссиям", callback_data="back_to_missions")]]
    back_markup = InlineKeyboardMarkup(back_button)
    
    await query.edit_message_text(
        f"{attacker_message}\nЧто бы укзать результат игры 'ответьте' на это сообщение указав счёт в формате [ваши очки] [очки оппонента], например:\n20 0",
        reply_markup=back_markup
    )

    # Отправляем сообщение с миссией дефендеру
    if defender_id:
        try:
            defender_message = build_mission_message(attacker_is_dominant, attacker_nickname)
            
            await context.bot.send_message(
                chat_id=defender_id, 
                text=f"Новая миссия:\n{defender_message}"
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
        await update.message.reply_text(
            "Ответ должен быть на сообщение с миссией. Пожалуйста, нажмите 'Ответить' на сообщение миссии и укажите счёт в формате '20 0'."
        )
        return MAIN_MENU

    # Validate score format
    try:
        counts = user_reply.split(' ')
        if len(counts) != 2:
            raise ValueError("Invalid format")
        submitter_score = int(counts[0])
        opponent_score = int(counts[1])
    except (ValueError, IndexError):
        await update.message.reply_text(
            "Неверный формат счёта. Пожалуйста, используйте формат '20 0' (ваш_счёт счёт_противника)."
        )
        return MAIN_MENU

    # Разделяем текст на строки
    lines = original_message.splitlines()

    # Ищем строку, начинающуюся с '#'
    mission_id_line = next(
        (line for line in lines if line.startswith('#')), None)
    if not mission_id_line:
        await update.message.reply_text("Не удалось определить миссию.")
        return MAIN_MENU
        
    # Извлекаем значение после решётки - это реальный mission_id из базы
    mission_id = int(mission_id_line[1:])
    
    # Находим активный battle_id для этой миссии и пользователя
    battle_id = await sqllite_helper.get_active_battle_id_for_mission(
        mission_id, update.effective_user.id)
    
    if not battle_id:
        logger.error(f"No active battle found for mission {mission_id} and user {update.effective_user.id}")
        await update.message.reply_text("Не найден активный бой для этой миссии.")
        return MAIN_MENU
    
    # Check if there's already a pending result for this battle
    existing_result = await sqllite_helper.get_battle_result(battle_id)
    if existing_result and existing_result['fstplayer_score'] is not None:
        await update.message.reply_text(
            "Для этой миссии уже ожидается подтверждение результата. "
            "Дождитесь подтверждения или отмены от противника."
        )
        return MAIN_MENU
    
    logger.info(f"Found battle_id {battle_id} for mission_id {mission_id}")
    
    # Get battle participants
    participants = await sqllite_helper.get_battle_participants(battle_id)
    if not participants:
        await update.message.reply_text("Ошибка: не удалось найти участников битвы.")
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
        await update.message.reply_text("Ошибка: вы не являетесь участником этой битвы.")
        return MAIN_MENU
    
    # Submit battle result (without storing submitter_id)
    success = await sqllite_helper.submit_battle_result(
        battle_id, fstplayer_score, sndplayer_score
    )
    
    if not success:
        await update.message.reply_text("Ошибка при сохранении результата.")
        return MAIN_MENU
    
    # Update mission status to 2 (pending confirmation)
    await sqllite_helper.update_mission_status(mission_id, 2)
    logger.info(f"Mission {mission_id} status set to 2 (pending confirmation)")
    
    # Get submitter and opponent nicknames
    submitter_nickname = await sqllite_helper.get_nickname_by_telegram_id(submitter_id)
    opponent_nickname = await sqllite_helper.get_nickname_by_telegram_id(opponent_id)
    
    # Determine winner
    if submitter_score > opponent_score:
        winner_text = f"Победитель: {submitter_nickname} ({submitter_score}:{opponent_score})"
    elif opponent_score > submitter_score:
        winner_text = f"Победитель: {opponent_nickname} ({submitter_score}:{opponent_score})"
    else:
        winner_text = f"Ничья ({submitter_score}:{opponent_score})"
    
    # Send confirmation request to opponent
    confirmation_message = (
        f"🎲 Результат миссии #{mission_id}\n\n"
        f"Игрок {submitter_nickname} ввёл результат:\n"
        f"{winner_text}\n\n"
        f"Подтвердите или отмените результат:"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_result_{battle_id}"),
            InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_result_{battle_id}")
        ]
    ])
    
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
    await update.message.reply_text(
        f"✅ Результат отправлен на подтверждение противнику.\n{winner_text}"
    )
    
    return MAIN_MENU


async def confirm_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for confirming a pending battle result."""
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    battle_id = int(query.data.replace("confirm_result_", ""))
    
    logger.info(f"User {user_id} confirming result for battle {battle_id}")
    
    # Get the battle result
    battle_result = await sqllite_helper.get_battle_result(battle_id)
    if not battle_result or battle_result['fstplayer_score'] is None:
        await query.edit_message_text("❌ Ошибка: результат не найден или уже обработан.")
        return MAIN_MENU
    
    # Get battle participants
    participants = await sqllite_helper.get_battle_participants(battle_id)
    if not participants:
        await query.edit_message_text("❌ Ошибка: не удалось найти участников битвы.")
        return MAIN_MENU
    
    fstplayer_id, sndplayer_id = participants
    
    # Verify that the user is a participant
    if user_id not in [fstplayer_id, sndplayer_id]:
        await query.edit_message_text("❌ Вы не являетесь участником этой битвы.")
        return MAIN_MENU
    
    # Determine the submitter (the one who is NOT confirming)
    submitter_id = sndplayer_id if user_id == fstplayer_id else fstplayer_id
    
    # Get mission_id
    mission_id = battle_result['mission_id']
    if not mission_id:
        await query.edit_message_text("❌ Ошибка: миссия не найдена.")
        return MAIN_MENU
    
    # Construct user_reply for existing functions
    user_reply = f"{battle_result['fstplayer_score']} {battle_result['sndplayer_score']}"
    
    try:
        # Apply the battle result using existing functions
        await mission_helper.write_battle_result(battle_id, user_reply)
        
        # Apply mission-specific rewards - use submitter_id as they originally entered the result
        rewards = await mission_helper.apply_mission_rewards(
            battle_id, user_reply, submitter_id
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
            submitter_id,
            scenario
        )
        
        # Update mission status to 3 (confirmed)
        await sqllite_helper.update_mission_status(mission_id, 3)
        logger.info(f"Mission {mission_id} status set to 3 (confirmed)")
        
        # Get nicknames for message
        submitter_nickname = await sqllite_helper.get_nickname_by_telegram_id(submitter_id)
        
        # Send success message
        await query.edit_message_text(
            f"✅ Результат подтверждён!\n"
            f"Счёт: {battle_result['fstplayer_score']}:{battle_result['sndplayer_score']}\n"
            f"Результаты применены к карте и рейтингу."
        )
        
        # Notify the submitter that result was confirmed
        try:
            confirmer_nickname = await sqllite_helper.get_nickname_by_telegram_id(user_id)
            await context.bot.send_message(
                chat_id=submitter_id,
                text=f"✅ Ваш результат для миссии #{mission_id} подтверждён игроком {confirmer_nickname}!"
            )
        except Exception as e:
            logger.error(f"Failed to notify submitter {submitter_id}: {e}")
        
    except Exception as e:
        logger.error(f"Error confirming result for battle {battle_id}: {e}", exc_info=True)
        await query.edit_message_text(f"❌ Ошибка при применении результата: {str(e)}")
        return MAIN_MENU
    
    return MAIN_MENU


async def cancel_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for canceling a pending battle result."""
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    battle_id = int(query.data.replace("cancel_result_", ""))
    
    logger.info(f"User {user_id} canceling result for battle {battle_id}")
    
    # Get the battle result
    battle_result = await sqllite_helper.get_battle_result(battle_id)
    if not battle_result or battle_result['fstplayer_score'] is None:
        await query.edit_message_text("❌ Ошибка: результат не найден или уже обработан.")
        return MAIN_MENU
    
    # Get battle participants
    participants = await sqllite_helper.get_battle_participants(battle_id)
    if not participants:
        await query.edit_message_text("❌ Ошибка: не удалось найти участников битвы.")
        return MAIN_MENU
    
    fstplayer_id, sndplayer_id = participants
    
    # Verify that the user is a participant
    if user_id not in [fstplayer_id, sndplayer_id]:
        await query.edit_message_text("❌ Вы не являетесь участником этой битвы.")
        return MAIN_MENU
    
    # Determine the submitter (the one who is NOT canceling)
    submitter_id = sndplayer_id if user_id == fstplayer_id else fstplayer_id
    
    # Get mission_id
    mission_id = battle_result['mission_id']
    if not mission_id:
        await query.edit_message_text("❌ Ошибка: миссия не найдена.")
        return MAIN_MENU
    
    try:
        # Clear the battle result
        await sqllite_helper.clear_battle_result(battle_id)
        
        # Reset mission status to 1 (active) so they can resubmit
        await sqllite_helper.update_mission_status(mission_id, 1)
        logger.info(f"Mission {mission_id} status reset to 1 (active)")
        
        await query.edit_message_text(
            f"❌ Результат отменён.\n"
            f"Миссия #{mission_id} открыта для повторного ввода результата."
        )
        
        # Notify the submitter that result was canceled
        try:
            canceler_nickname = await sqllite_helper.get_nickname_by_telegram_id(user_id)
            await context.bot.send_message(
                chat_id=submitter_id,
                text=f"❌ Ваш результат для миссии #{mission_id} был отменён игроком {canceler_nickname}. Вы можете ввести новый результат."
            )
        except Exception as e:
            logger.error(f"Failed to notify submitter {submitter_id}: {e}")
        
    except Exception as e:
        logger.error(f"Error canceling result for battle {battle_id}: {e}", exc_info=True)
        await query.edit_message_text(f"❌ Ошибка при отмене результата: {str(e)}")
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
        await query.edit_message_text("❌ У вас нет прав администратора")
        return MAIN_MENU
    
    # Get all pending missions
    pending_missions = await sqllite_helper.get_all_pending_missions()
    
    if not pending_missions:
        await query.edit_message_text(
            "✅ Нет миссий ожидающих подтверждения.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Назад", callback_data="admin_menu")
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
            battle_result = await sqllite_helper.get_battle_result(battle_id)
            if battle_result and battle_result['fstplayer_score'] is not None:
                score_text = f"{battle_result['fstplayer_score']}:{battle_result['sndplayer_score']}"
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
    
    keyboard.append([
        InlineKeyboardButton("« Назад в админ меню", callback_data="admin_menu")
    ])
    
    markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"⏳ Миссии ожидающие подтверждения ({len(pending_missions)}):\n\n"
        "Выберите миссию для подтверждения результата:",
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
        await query.edit_message_text("❌ У вас нет прав администратора")
        return MAIN_MENU
    
    # Extract mission_id from callback data
    mission_id = int(query.data.split(':')[1])
    
    # Get battle_id for this mission
    battle_id = await sqllite_helper.get_battle_id_by_mission_id(mission_id)
    if not battle_id:
        await query.edit_message_text(
            f"❌ Не найден бой для миссии #{mission_id}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Назад", callback_data="admin_pending_confirmations")
            ]])
        )
        return MAIN_MENU
    
    # Get battle result
    battle_result = await sqllite_helper.get_battle_result(battle_id)
    if not battle_result or battle_result['fstplayer_score'] is None:
        await query.edit_message_text(
            f"❌ Не найден ожидающий результат для миссии #{mission_id}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Назад", callback_data="admin_pending_confirmations")
            ]])
        )
        return MAIN_MENU
    
    # Get mission details
    mission_details = await sqllite_helper.get_mission_details(mission_id)
    if not mission_details:
        await query.edit_message_text(f"❌ Миссия #{mission_id} не найдена")
        return MAIN_MENU
    
    # Get participant names
    participants = await sqllite_helper.get_battle_participants(battle_id)
    if participants:
        fstplayer_id, sndplayer_id = participants
        fstplayer_name = await sqllite_helper.get_nickname_by_telegram_id(fstplayer_id)
        sndplayer_name = await sqllite_helper.get_nickname_by_telegram_id(sndplayer_id)
        
        participants_text = (
            f"👥 Участники:\n"
            f"  • {fstplayer_name} ({battle_result['fstplayer_score']})\n"
            f"  • {sndplayer_name} ({battle_result['sndplayer_score']})\n"
        )
    else:
        participants_text = "👥 Участники: неизвестны\n"
    
    # Determine winner
    if battle_result['fstplayer_score'] > battle_result['sndplayer_score']:
        winner_text = f"🏆 Победитель: {fstplayer_name}"
    elif battle_result['sndplayer_score'] > battle_result['fstplayer_score']:
        winner_text = f"🏆 Победитель: {sndplayer_name}"
    else:
        winner_text = "🤝 Ничья"
    
    message_text = (
        f"🎲 Миссия #{mission_id}\n"
        f"📜 Правила: {mission_details.rules if mission_details else 'неизвестно'}\n"
        f"📅 Создана: {mission_details.created_date if mission_details else 'неизвестно'}\n\n"
        f"{participants_text}\n"
        f"{winner_text}\n\n"
        f"Подтвердить результат?"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"admin_do_confirm:{battle_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"admin_do_reject:{battle_id}")
        ],
        [
            InlineKeyboardButton("« Назад", callback_data="admin_pending_confirmations")
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
        await query.edit_message_text("❌ У вас нет прав администратора")
        return MAIN_MENU
    
    # Extract battle_id from callback data
    battle_id = int(query.data.split(':')[1])
    
    # Get battle result
    battle_result = await sqllite_helper.get_battle_result(battle_id)
    if not battle_result or battle_result['fstplayer_score'] is None:
        await query.edit_message_text("❌ Результат не найден или уже обработан")
        return MAIN_MENU
    
    # Get mission_id
    mission_id = battle_result['mission_id']
    if not mission_id:
        await query.edit_message_text("❌ Миссия не найдена")
        return MAIN_MENU
    
    # Get battle participants
    participants = await sqllite_helper.get_battle_participants(battle_id)
    if not participants:
        await query.edit_message_text("❌ Не удалось найти участников битвы")
        return MAIN_MENU
    
    # Use first player (attacker) as the submitter for reward/map purposes
    fstplayer_id, sndplayer_id = participants
    
    # Construct user_reply for existing functions
    user_reply = f"{battle_result['fstplayer_score']} {battle_result['sndplayer_score']}"
    
    try:
        # Apply the battle result
        await mission_helper.write_battle_result(battle_id, user_reply)
        
        # Apply mission-specific rewards (use first player as submitter)
        rewards = await mission_helper.apply_mission_rewards(
            battle_id, user_reply, fstplayer_id
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
            fstplayer_id,
            scenario
        )
        
        # Update mission status to 3 (confirmed)
        await sqllite_helper.update_mission_status(mission_id, 3)
        logger.info(f"Admin confirmed mission {mission_id}, status set to 3")
        
        # Notify participants
        if participants:
            for participant_id in participants:
                try:
                    await context.bot.send_message(
                        chat_id=participant_id,
                        text=f"✅ Администратор подтвердил результат миссии #{mission_id}\n"
                             f"Счёт: {battle_result['fstplayer_score']}:{battle_result['sndplayer_score']}"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify participant {participant_id}: {e}")
        
        await query.edit_message_text(
            f"✅ Результат миссии #{mission_id} подтверждён!\n"
            f"Счёт: {pending_result.fstplayer_score}:{pending_result.sndplayer_score}\n"
            f"✅ Результат миссии #{mission_id} подтверждён!\n"
            f"Счёт: {battle_result['fstplayer_score']}:{battle_result['sndplayer_score']}\n"
            f"Результаты применены.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« К списку миссий", callback_data="admin_pending_confirmations")
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error confirming mission {mission_id}: {e}", exc_info=True)
        await query.edit_message_text(f"❌ Ошибка при подтверждении: {str(e)}")
    
    return MAIN_MENU


async def admin_do_reject_mission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Admin rejects a pending mission result."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    # Check if user is admin
    is_admin = await sqllite_helper.is_user_admin(user_id)
    if not is_admin:
        await query.edit_message_text("❌ У вас нет прав администратора")
        return MAIN_MENU
    
    # Extract battle_id from callback data
    battle_id = int(query.data.split(':')[1])
    
    # Get battle result
    battle_result = await sqllite_helper.get_battle_result(battle_id)
    if not battle_result or battle_result['fstplayer_score'] is None:
        await query.edit_message_text("❌ Результат не найден или уже обработан")
        return MAIN_MENU
    
    # Get mission_id
    mission_id = battle_result['mission_id']
    if not mission_id:
        await query.edit_message_text("❌ Миссия не найдена")
        return MAIN_MENU
    
    try:
        # Clear the battle result
        await sqllite_helper.clear_battle_result(battle_id)
        
        # Reset mission status to 1 (active)
        await sqllite_helper.update_mission_status(mission_id, 1)
        logger.info(f"Admin rejected mission {mission_id}, status reset to 1")
        
        # Notify participants
        participants = await sqllite_helper.get_battle_participants(battle_id)
        if participants:
            for participant_id in participants:
                try:
                    await context.bot.send_message(
                        chat_id=participant_id,
                        text=f"❌ Администратор отклонил результат миссии #{mission_id}\n"
                             "Вы можете ввести новый результат."
                    )
                except Exception as e:
                    logger.error(f"Failed to notify participant {participant_id}: {e}")
        
        await query.edit_message_text(
            f"❌ Результат миссии #{mission_id} отклонён.\n"
            f"Миссия открыта для повторного ввода результата.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« К списку миссий", callback_data="admin_pending_confirmations")
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error rejecting mission {mission_id}: {e}", exc_info=True)
        await query.edit_message_text(f"❌ Ошибка при отклонении: {str(e)}")
    
    return MAIN_MENU


async def debug_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug handler for unmatched callbacks"""
    query = update.callback_query
    user_id = update.effective_user.id
    logger.warning(f"Unmatched callback from user {user_id}: '{query.data}' in current state")
    logger.warning(f"Current conversation state: {context.user_data}")
    await query.answer(f"Debug: Callback '{query.data}' not handled")
    return ConversationHandler.END

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
                CallbackQueryHandler(admin_edit_alliances, pattern='^admin_edit_alliances$')
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
