from asyncio.windows_events import NULL
from telegram import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler

import config
import players_helper
import keyboard_constructor
import sqllite_helper

START_ROUTES, END_ROUTES = range(2)
# Callback data
ONE, TWO, THREE, FOUR = range(4)

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    userId = update.effective_user.id
    rules = await keyboard_constructor.get_keyboard_rules_keyboard_for_user(userId)
    menu = InlineKeyboardMarkup(rules)
    await update.message.reply_text(f'Choose the rules {update.effective_user.first_name}', reply_markup=menu)
    
async def im_in(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    opponents = players_helper.get_opponents(update.effective_user)
    for opponent in opponents:
        reply_text += opponent
        players_helper.notify(opponent)
    opponnentsContacts = [[KeyboardButton("Kill Team",request_contact="")]]
    menu = ReplyKeyboardMarkup(opponnentsContacts)
    await update.message.reply_text(f'You faced with {reply_text}', reply_markup=menu)
    
async def test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'You faced')

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    when_markup = await keyboard_constructor.this_week()
    await sqllite_helper.insert_to_schedule(NULL, query.data, update.effective_user.id)
    menu = InlineKeyboardMarkup(when_markup)
    await query.edit_message_text(text=f"Selected option: {query.data}", reply_markup=menu)

bot = ApplicationBuilder().token(config.crusade_care_bot_telegram_token).build()

conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", hello)],
        states={
            START_ROUTES: [
                CallbackQueryHandler(one, pattern="^" + str(ONE) + "$"),
                CallbackQueryHandler(two, pattern="^" + str(TWO) + "$"),
                CallbackQueryHandler(three, pattern="^" + str(THREE) + "$"),
                CallbackQueryHandler(four, pattern="^" + str(FOUR) + "$"),
            ],
            END_ROUTES: [
                CallbackQueryHandler(start_over, pattern="^" + str(ONE) + "$"),
                CallbackQueryHandler(end, pattern="^" + str(TWO) + "$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

bot.add_handler(CommandHandler("start", hello))
bot.add_handler(CommandHandler("imin", im_in))
bot.add_handler(CommandHandler("Battlefleet", test))
bot.add_handler(CallbackQueryHandler(button))

bot.run_polling()