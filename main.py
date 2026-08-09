from telegram.ext import Application

from config import TOKEN
from buttons.start import start_handler
from buttons.menu import menu_handler


app = Application.builder().token(TOKEN).build()

start_handler(app)
menu_handler(app)

print("✅ Bot Running...")

app.run_polling()