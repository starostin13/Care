from asyncio.windows_events import NULL
from datetime import datetime
from msilib import sequence
from telegram import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler

import config
import players_helper
import keyboard_constructor
import logging
import sqllite_helper

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

MAIN_MENU, SETTINGS, GAMES, SCHEDULE = range(4)
# Callback data
ONE, TWO, THREE, FOUR = range(4)
TYPING_CHOICE, TYPING_REPLY = range(2)

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
    await query.answer()
    await query.edit_message_text(f'You will faced with')
    for opponent in opponents:
        await update.effective_chat.send_contact(first_name="asdsad", username="@starostin13")
        #reply_text += opponent
        #players_helper.notify(opponent)
        #await query.edit_message_text("")
        #await query.edit_message_text(opponent[0])
    
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

async def input_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.split(' ')[1]
    if text:
        query = update.callback_query
        await players_helper.set_name(update.effective_user.id, text)
    
        await update.message.reply_text(f"Your {text}? Yes, I would love to hear about that!")

async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query    
    await query.answer()
    await query.edit_message_text(
        'Just type "/ setname MyName"'
    )
    return TYPING_CHOICE

async def setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    menu = await keyboard_constructor.setting(update.effective_user.id)
    query = update.callback_query    
    await query.answer()
    markup = InlineKeyboardMarkup(menu)
    await query.edit_message_text("Your settings:", reply_markup=markup)
    return MAIN_MENU

bot = ApplicationBuilder().token(config.crusade_care_bot_telegram_token).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", hello),
                  ],
    states={
        MAIN_MENU: [
            CallbackQueryHandler(set_name, pattern='^requestsetname$'),
            CallbackQueryHandler(setting, pattern='^callsettings$'),
            CallbackQueryHandler(appoint, pattern="^" + 'callgame' + "$")
        ],
        SETTINGS: [
            CallbackQueryHandler(im_in)
        ],
        GAMES: [            
            CallbackQueryHandler(button, pattern='rule')
        ],
        SCHEDULE: [
            CallbackQueryHandler(im_in)
        ]    
    },
    fallbacks=[CommandHandler("start", hello)],
    )

bot.add_handler(conv_handler)
bot.add_handler(CommandHandler("setname", input_name))

bot.run_polling()