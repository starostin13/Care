from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from services.user_service import set_user_name

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

async def input_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.split(' ')[1]
    if text:
        await players_helper.set_name(update.effective_user.id, text)
        await update.message.reply_text(f"Your name {text} has been saved!")

async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.split(' ')[1]
    if text:
        await set_user_name(update.effective_user.id, text)
        await update.message.reply_text(f"Your name has been set to {text}!")
    else:
        await update.message.reply_text("Please provide a name.")