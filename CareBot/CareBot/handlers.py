#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8
from asyncio.windows_events import NULL
from datetime import datetime
from msilib import sequence
from telegram import CallbackQuery, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

import config
import players_helper
import keyboard_constructor
import logging
import sqllite_helper
import mission_helper

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
    custom_keyboard = [[ con_keyboard ]]
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
    # Получаем миссию из базы данных
    mission = await mission_helper.get_mission()
    query = update.callback_query
    data = query.data  # Получаем данные из нажатой кнопки
    
    # Преобразуем миссию в текст
    text = '\n'.join(
        f'#{mission[i]}' if i == 4 else str(item or '')
        for i, item in enumerate(mission)
    )

    # Отправляем текст миссии текущему пользователю
    await query.edit_message_text(f"{text}\nЧто бы укзать результат игры 'ответьте' на это сообщение указав счёт в формате [ваши очки] [очки оппонента], например:\n20 0")

    # Получаем список всех участников события
    participants = await sqllite_helper.get_event_participants(data.rsplit('_', 1)[-1])

    # Рассылаем сообщение с миссией всем участникам
    for participant_id in participants:
        if participant_id != update.effective_user.id:  # Исключаем текущего пользователя
            try:
                await context.bot.send_message(chat_id=participant_id, text=f"Новая миссия:\n{text}")
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения пользователю {participant_id}: {e}")

    return MISSIONS


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userId = update.effective_user.id

    await players_helper.add_warmaster(userId)
    menu = await keyboard_constructor.get_main_menu(userId)
    menu_markup = InlineKeyboardMarkup(menu)
    query = update.callback_query
    await update.message.reply_text("Hi", reply_markup=menu_markup)
    #await query.answer()
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
    sqllite_helper.insert_to_schedule(
        datetime.strptime(data_arr[0],'%c'),
        data_arr[1].split(':')[1],
        update.effective_user.id)
    opponents = await players_helper.get_opponents(update.effective_user.id, data)
    #await query.answer()
    await query.edit_message_text(f'You will faced with')
    for opponent in opponents:
        if opponent[1] is not None:
            await update.effective_chat.send_contact(first_name=str(opponent[0]), phone_number=opponent[1])
        #await context.bot.send_message(job.chat_id, text=f"Beep! {job.data} seconds are over!")
    
async def end_poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'You faced')
    return SETTINGS

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    # await query.answer()
    when_markup = await keyboard_constructor.this_week(query.data)
    #await sqllite_helper.insert_to_schedule(NULL, query.data, update.effective_user.id)
    menu = InlineKeyboardMarkup(when_markup)
    await query.edit_message_text(text=f"Selected option: {query.data}", reply_markup=menu)
    return SCHEDULE

# Handler to process the reply to the message from show_missions
async def handle_mission_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Retrieve the original message's text and user's reply
    original_message = update.message.reply_to_message.text
    user_reply = update.message.text

    # Example: You can log the interaction or perform some action based on the reply
    logger.info(f"User {update.effective_user.id} replied to '{original_message}' with '{user_reply}'")

    # Разделяем текст на строки
    lines = original_message.splitlines()

    # Ищем строку, начинающуюся с '#'
    battle_id = [line for line in lines if line.startswith('#')]
    await mission_helper.write_battle_result(battle_id[0], user_reply)

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
    menu = await keyboard_constructor.setting(update.effective_user.id)
    query = update.callback_query    
    await query.answer()
    markup = InlineKeyboardMarkup(menu)
    await query.edit_message_text("Your settings:", reply_markup=markup)
    return MAIN_MENU

async def show_missions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    menu = await keyboard_constructor.today_schedule(update.effective_user.id)
    markup = InlineKeyboardMarkup(menu)
    query = update.callback_query
    await query.edit_message_text("Your appointments:", reply_markup=markup)
    return MISSIONS

bot = ApplicationBuilder().token(config.crusade_care_bot_telegram_token).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", hello),
                  ],
    states={
        MAIN_MENU: [
            CallbackQueryHandler(set_name, pattern='^requestsetname$'),
            CallbackQueryHandler(setting, pattern='^callsettings$'),
            CallbackQueryHandler(appoint, pattern="^" + 'callgame' + "$"),
            CallbackQueryHandler(registration_call, pattern='^registration$'),
            CallbackQueryHandler(show_missions, pattern='^callmissions$')
        ],
        SETTINGS: [
            CallbackQueryHandler(im_in)
        ],
        GAMES: [            
            CallbackQueryHandler(button, pattern='rule')
        ],
        SCHEDULE: [
            CallbackQueryHandler(im_in)
        ],
        MISSIONS: [
            CallbackQueryHandler(get_the_mission)    
        ]
    },
    fallbacks=[CommandHandler("start", hello)],
    )

# Handler for catching replies to the bot's messages, specifically replies to get_the_mission
bot.add_handler(MessageHandler(filters.REPLY & filters.TEXT, handle_mission_reply))
bot.add_handler(conv_handler)
bot.add_handler(CommandHandler("setname", input_name))
bot.add_handler(CommandHandler("regme", contact))
bot.add_handler(MessageHandler(filters.CONTACT, contact_callback))

bot.run_polling()