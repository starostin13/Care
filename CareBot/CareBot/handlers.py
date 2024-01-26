from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')


app = ApplicationBuilder().token(crusade_care_bot_telegram_token).build()

app.add_handler(CommandHandler("hello", hello))

app.run_polling()