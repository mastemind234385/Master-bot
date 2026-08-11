import os

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.ext import MessageHandler, filters

from buttons.menu import menu, keyboard

TOKEN = os.getenv("TOKEN")

print("TOKEN =", TOKEN)

if not TOKEN:
    raise ValueError("TOKEN not found!")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\nনিচের Menu থেকে একটি অপশন নির্বাচন করুন।",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))

print("Bot running...")

app.run_polling()
