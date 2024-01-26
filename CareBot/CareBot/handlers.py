from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config
import players_helper

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')
    
async def im_in(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    opponents = players_helper.get_opponents(update.effective_user)
    for opponent in opponents:
        reply_text += opponent
        players_helper.notify(opponent)
    await update.message.reply_text(f'You faced with {reply_text}')


app = ApplicationBuilder().token(config.crusade_care_bot_telegram_token).build()

app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("hello", im_in))

app.run_polling()