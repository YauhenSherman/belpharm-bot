from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from config import USER_MAP
from keyboards.reply import (
    get_main_keyboard,
    get_status_keyboard,
    build_codes_keyboard,
    build_districts_keyboard,
    get_stand_format_keyboard,
)
from services.sheets import get_rows, update_pharmacy_result
from services.reports import send_group_report
from services.pharmacy import (
    get_user_name,
    build_pharmacy_card,
    find_row_by_code,
)
from state.memory import (
    user_state,
    selected_pharmacy,
    pending_status,
    pending_stand_format,
    selected_district,
)
from utils.text import normalize_text
from utils.logger import logger


STATUSES = [
    "Согласовано",
    "Отказ",
    "Повторный визит",
    "Не существует",
    "Обслуживается",
]

STAND_FORMATS = [
    "А4 вертикаль",
    "А4 горизонт",
    "А5",
    "А6 наклейка",
]


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    if update.effective_chat.type != "private":
        return

    user_id = update.effective_user.id
    text = update.message.text.strip()
    telegram_id = update.message.from_user.id

    if user_id not in USER_MAP:
        await update.message.reply_text("⛔ Доступ запрещён.")
        return

    if text == "Меню":
        user_state.pop(telegram_id, None)
        pending_status.pop(telegram_id, None)
        pending_stand_format.pop(telegram_id, None)
        selected_district.pop(telegram_id, None)

        await update.message.reply_text("Главное меню 👇", reply_markup=get_main_keyboard())
        return

    rows = get_rows()

    # выбор формата
    if user_state.get(telegram_id) == "waiting_stand_format":
        if text == "Отмена":
            user_state.pop(telegram_id, None)
            pending_status.pop(telegram_id, None)
            pending_stand_format.pop(telegram_id, None)

            await update.message.reply_text("Отменено", reply_markup=get_status_keyboard())
            return

        if text not in STAND_FORMATS:
            await update.message.reply_text("Выбери формат 👇", reply_markup=get_stand_format_keyboard())
            return

        pending_stand_format[telegram_id] = text
        user_state[telegram_id] = "waiting_comment"

        await update.message.reply_text("Напиши комментарий", reply_markup=ReplyKeyboardMarkup([["Меню"]], resize_keyboard=True))
        return

    # комментарий
    if user_state.get(telegram_id) == "waiting_comment":
        code = selected_pharmacy.get(telegram_id)
        status = pending_status.get(telegram_id)
        stand_format = pending_stand_format.get(telegram_id)

        comment = text

        saved_row = update_pharmacy_result(
            code=code,
            status=status,
            comment=comment,
            stand_format=stand_format,
            normalize_text_func=normalize_text,
        )

        user_state.pop(telegram_id, None)
        pending_status.pop(telegram_id, None)
        pending_stand_format.pop(telegram_id, None)

        await update.message.reply_text(
            f"Сохранено ✅\n{status}\n{stand_format or ''}\n{comment}",
            reply_markup=get_main_keyboard(),
        )
        return

    # выбор статуса
    if text in STATUSES:
        code = selected_pharmacy.get(telegram_id)

        if not code:
            await update.message.reply_text("Сначала выбери аптеку")
            return

        pending_status[telegram_id] = text

        if text == "Согласовано":
            user_state[telegram_id] = "waiting_stand_format"
            await update.message.reply_text("Выбери формат 👇", reply_markup=get_stand_format_keyboard())
            return

        user_state[telegram_id] = "waiting_comment"
        await update.message.reply_text("Напиши комментарий")
        return

    # выбор аптеки
    found = find_row_by_code(rows, text)
    if found:
        selected_pharmacy[telegram_id] = found.get("КОД")

        await update.message.reply_text(
            build_pharmacy_card(found),
            reply_markup=get_status_keyboard(),
        )
        return

    await update.message.reply_text("Выбери кнопку", reply_markup=get_main_keyboard())