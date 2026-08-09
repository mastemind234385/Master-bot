from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes

keyboard = [
    ["🚀 Start", "❓ Help"],
    ["👨‍💻 Developer", "🕒 Time"],
    ["🕌 Prayer Time", "⏳ Prayer Remaining"],
    ["🎥 Video Downloader", "🔊 Text To Voice"]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\nনিচের Menu থেকে একটি অপশন নির্বাচন করুন।",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

def start_handler(app):
    app.add_handler(CommandHandler("start", start))