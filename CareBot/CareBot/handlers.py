#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8
import notification_service
import localization
import migrate_db
import mission_helper
import sqllite_helper
import logging
import keyboard_constructor
import players_helper
import config
import map_helper
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from telegram import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
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
    sqllite_helper.register_warmaster(userid, phone)


async def get_the_mission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # update.callback_query.data 'mission_sch_2'
    mission_number = int(
        update.callback_query.data.replace("mission_sch_", ""))
    rules = await sqllite_helper.get_rules_of_mission(mission_number)
    # Получаем миссию из базы данных
    mission = await mission_helper.get_mission(rules=rules)
    query = update.callback_query
    data = query.data  # Получаем данные из нажатой кнопки
    index_of_mission_id = 2

    # Получаем список всех участников события
    participants = await sqllite_helper.get_event_participants(data.rsplit('_', 1)[-1])

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

    # Get localized greeting message
    user_name = update.effective_user.first_name or "User"
    greeting_text = await localization.get_text_for_user(
        userId, 'main_menu_greeting', name=user_name
    )

    await query.edit_message_text(greeting_text, reply_markup=menu_markup)
    logger.info("Successfully returned to main menu")
    return MAIN_MENU


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userId = update.effective_user.id
    logger.info(f"hello function called by user {userId}")

    await players_helper.add_warmaster(userId)
    menu = await keyboard_constructor.get_main_menu(userId)
    menu_markup = InlineKeyboardMarkup(menu)

    # Get localized greeting message
    user_name = update.effective_user.first_name or "User"
    greeting_text = await localization.get_text_for_user(
        userId, 'main_menu_greeting', name=user_name
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
    await sqllite_helper.insert_to_schedule(
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
    text = update.message.text.split(' ')[1]
    if text:
        query = update.callback_query
        await players_helper.set_name(update.effective_user.id, text)

        await update.message.reply_text(f"Your {text}? Yes, I would love to hear about that!")


async def registration_call(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        'Just type or click on it /regme'
    )


async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        'Just type "/ setname MyName. Without spaces."'
    )
    return TYPING_CHOICE


async def setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"setting function called")
    user_id = update.effective_user.id
    menu = await keyboard_constructor.setting(user_id)
    query = update.callback_query
    await query.answer()
    markup = InlineKeyboardMarkup(menu)

    settings_text = await localization.get_text_for_user(user_id, "settings_title")
    await query.edit_message_text(settings_text, reply_markup=markup)
    logger.info("Returning to SETTINGS state")
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
    await sqllite_helper.set_language(user_id, language)
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
    new_value = await sqllite_helper.toggle_notifications(user_id)
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


async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to the Crusade Bot! Please type /start to begin.")

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
                back_to_settings, pattern='^back_to_settings$')
        ],
        SETTINGS: [
            CallbackQueryHandler(back_to_main_menu, pattern='^back_to_main$'),
            CallbackQueryHandler(back_to_main_menu, pattern='^start$'),
            CallbackQueryHandler(change_language, pattern='^changelanguage$'),
            CallbackQueryHandler(set_language, pattern='^lang:'),
            CallbackQueryHandler(toggle_notifications,
                                 pattern='^togglenotifications$')
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
bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, welcome))
bot.add_handler(CommandHandler("setname", input_name))
bot.add_handler(CommandHandler("regme", contact))
bot.add_handler(MessageHandler(filters.CONTACT, contact_callback))

bot.run_polling()
