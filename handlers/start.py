from telegram import Update
from telegram.ext import ContextTypes

from keyboards.reply import get_main_keyboard


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    await update.message.reply_text(
        "Привет! Я бот для обхода аптек 👇",
        reply_markup=get_main_keyboard(),
    )