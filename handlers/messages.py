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
    find_row_by_label,
)
from state.memory import (
    user_state,
    selected_pharmacy_uid,
    selected_pharmacy_label,
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
    user_name = USER_MAP.get(user_id, "Неизвестный")
    telegram_id = update.message.from_user.id

    if user_id not in USER_MAP:
        logger.warning("Запрещённый доступ | user_id=%s | text=%r", user_id, text)
        await update.message.reply_text("⛔ Доступ запрещён.")
        return

    logger.info("%s (%s): %s", user_name, user_id, text)

    if text == "Меню":
        user_state.pop(telegram_id, None)
        pending_status.pop(telegram_id, None)
        pending_stand_format.pop(telegram_id, None)
        selected_pharmacy_uid.pop(telegram_id, None)
        selected_pharmacy_label.pop(telegram_id, None)
        selected_district.pop(telegram_id, None)

        await update.message.reply_text(
            "Главное меню 👇",
            reply_markup=get_main_keyboard(),
        )
        return

    rows = get_rows()

    if user_state.get(telegram_id) == "waiting_stand_format":
        if text == "Отмена":
            user_state.pop(telegram_id, None)
            pending_status.pop(telegram_id, None)
            pending_stand_format.pop(telegram_id, None)

            await update.message.reply_text(
                "Выбор формата отменён.",
                reply_markup=get_status_keyboard(),
            )
            return

        if text not in STAND_FORMATS:
            await update.message.reply_text(
                "Выбери формат стенда кнопкой ниже.",
                reply_markup=get_stand_format_keyboard(),
            )
            return

        pending_stand_format[telegram_id] = text
        user_state[telegram_id] = "waiting_comment"

        await update.message.reply_text(
            "Напиши комментарий к этой аптеке.",
            reply_markup=ReplyKeyboardMarkup([["Меню"]], resize_keyboard=True),
        )
        return

    if user_state.get(telegram_id) == "waiting_comment":
        pharmacy_uid = selected_pharmacy_uid.get(telegram_id)
        pharmacy_label = selected_pharmacy_label.get(telegram_id)
        status = pending_status.get(telegram_id)
        stand_format = pending_stand_format.get(telegram_id)

        if not pharmacy_uid or not status:
            await update.message.reply_text(
                "Сначала выбери аптеку и статус.",
                reply_markup=get_main_keyboard(),
            )
            return

        if status == "Согласовано" and not stand_format:
            user_state[telegram_id] = "waiting_stand_format"
            await update.message.reply_text(
                "Сначала выбери формат стенда.",
                reply_markup=get_stand_format_keyboard(),
            )
            return

        comment = text
        saved_row = update_pharmacy_result(
            uid=pharmacy_uid,
            status=status,
            comment=comment,
            stand_format=stand_format,
            normalize_text_func=normalize_text,
        )

        report_user_name = get_user_name(telegram_id, USER_MAP) or f"ID {telegram_id}"
        pharmacy_display = (
            str(saved_row.get("LABEL", ""))
            if saved_row
            else str(pharmacy_label or pharmacy_uid)
        )
        pharmacy_code = (
            str(saved_row.get("КОД", ""))
            if saved_row
            else str(pharmacy_label or pharmacy_uid)
        )
        address = str(saved_row.get("Адрес", "")) if saved_row else ""

        await send_group_report(
            context=context,
            user_name=report_user_name,
            pharmacy_code=pharmacy_code,
            address=address,
            status=status,
            comment=comment,
            stand_format=stand_format,
        )

        user_state.pop(telegram_id, None)
        pending_status.pop(telegram_id, None)
        pending_stand_format.pop(telegram_id, None)
        selected_pharmacy_uid.pop(telegram_id, None)
        selected_pharmacy_label.pop(telegram_id, None)

        saved_message = f"Сохранено ✅\n\nСтатус: {status}"
        saved_message += f"\nАптека: {pharmacy_display}"
        if stand_format:
            saved_message += f"\nФормат: {stand_format}"
        saved_message += f"\nКомментарий: {comment}"

        await update.message.reply_text(
            saved_message,
            reply_markup=get_main_keyboard(),
        )
        return

    if text in STATUSES:
        pharmacy_uid = selected_pharmacy_uid.get(telegram_id)

        if not pharmacy_uid:
            await update.message.reply_text(
                "Сначала выбери аптеку.",
                reply_markup=get_main_keyboard(),
            )
            return

        pending_status[telegram_id] = text
        pending_stand_format.pop(telegram_id, None)

        if text == "Согласовано":
            user_state[telegram_id] = "waiting_stand_format"
            await update.message.reply_text(
                "Выбери формат стенда 👇",
                reply_markup=get_stand_format_keyboard(),
            )
            return

        user_state[telegram_id] = "waiting_comment"
        await update.message.reply_text(
            "Напиши комментарий к этой аптеке.",
            reply_markup=ReplyKeyboardMarkup([["Меню"]], resize_keyboard=True),
        )
        return

    if user_state.get(telegram_id) == "waiting_district":
        district_rows = [
            row for row in rows
            if str(row.get("Район", "")).strip() == text
        ]

        if not district_rows:
            await update.message.reply_text(
                "Район не найден. Нажми кнопку района ещё раз.",
                reply_markup=get_main_keyboard(),
            )
            return

        selected_district[telegram_id] = text
        user_state[telegram_id] = "district_selected"

        labels = [str(row.get("LABEL", "")).strip() for row in district_rows if row.get("LABEL")]
        preview = [
            f"• {row.get('КОД', '')} | {row.get('Адрес', '')}"
            for row in district_rows[:10]
        ]

        message = (
            f"Район: {text}\n\n"
            + "\n".join(preview)
            + "\n\nНажми кнопку с аптекой."
        )

        if len(district_rows) > 10:
            message += f"\n\nВсего аптек в районе: {len(district_rows)}"

        await update.message.reply_text(
            message,
            reply_markup=build_codes_keyboard(labels),
        )
        return

    found_row = find_row_by_label(rows, text)
    if found_row:
        selected_pharmacy_uid[telegram_id] = found_row.get("UID")
        selected_pharmacy_label[telegram_id] = found_row.get("LABEL")

        await update.message.reply_text(
            build_pharmacy_card(found_row),
            reply_markup=get_status_keyboard(),
        )
        return

    if text == "Мои аптеки":
        current_user_name = get_user_name(telegram_id, USER_MAP)

        if not current_user_name:
            await update.message.reply_text(
                f"Твой Telegram ID: {telegram_id}\n"
                f"Я пока не знаю, кто ты в таблице.\n"
                f"Добавь этот ID в USER_MAP.",
                reply_markup=get_main_keyboard(),
            )
            return

        my_rows = []
        for row in rows:
            responsible = str(row.get("ОТВЕТСТВЕННЫЙ", "")).strip()
            if responsible == current_user_name:
                my_rows.append(row)

        if not my_rows:
            await update.message.reply_text(
                f"Для {current_user_name} аптеки не найдены.",
                reply_markup=get_main_keyboard(),
            )
            return

        labels = [str(row.get("LABEL", "")).strip() for row in my_rows if row.get("LABEL")]
        preview = [
            f"• {row.get('КОД', '')} | {row.get('Адрес', '')}"
            for row in my_rows[:10]
        ]

        message = (
            f"Мои аптеки ({current_user_name}):\n\n"
            + "\n".join(preview)
            + "\n\nНажми кнопку с аптекой."
        )

        if len(my_rows) > 10:
            message += f"\n\nВсего аптек: {len(my_rows)}"

        await update.message.reply_text(
            message,
            reply_markup=build_codes_keyboard(labels),
        )
        return

    if text == "Свободные аптеки":
        free_rows = []

        for row in rows:
            responsible = str(row.get("ОТВЕТСТВЕННЫЙ", "")).strip()
            status = str(row.get("Результаты согласования", "")).strip()
            stand = str(row.get("ЕСТЬ СТЕНД (ГРУППА)", "")).strip()

            if not responsible or not status or not stand:
                free_rows.append(row)

        if not free_rows:
            await update.message.reply_text(
                "Свободных аптек нет 🎉",
                reply_markup=get_main_keyboard(),
            )
            return

        labels = [str(row.get("LABEL", "")).strip() for row in free_rows if row.get("LABEL")]
        preview = [
            f"• {row.get('КОД', '')} | {row.get('Адрес', '')}"
            for row in free_rows[:10]
        ]

        message = (
            "Свободные аптеки:\n\n"
            + "\n".join(preview)
            + "\n\nНажми кнопку с аптекой."
        )

        if len(free_rows) > 10:
            message += f"\n\nВсего аптек: {len(free_rows)}"

        await update.message.reply_text(
            message,
            reply_markup=build_codes_keyboard(labels),
        )
        return

    if text == "По району":
        districts = sorted(
            {
                str(row.get("Район", "")).strip()
                for row in rows
                if str(row.get("Район", "")).strip()
            }
        )

        if not districts:
            await update.message.reply_text(
                "Районы не найдены.",
                reply_markup=get_main_keyboard(),
            )
            return

        user_state[telegram_id] = "waiting_district"

        await update.message.reply_text(
            "Выбери район 👇",
            reply_markup=build_districts_keyboard(districts),
        )
        return

    if text == "Статистика":
        total = len(rows)
        agreed = 0
        refused = 0
        revisit = 0
        missing = 0

        for row in rows:
            status = str(row.get("Результаты согласования", "")).strip()

            if status == "Согласовано":
                agreed += 1
            elif status == "Отказ":
                refused += 1
            elif status == "Повторный визит":
                revisit += 1
            elif not status:
                missing += 1

        message = (
            "📊 Статистика\n\n"
            f"Всего аптек: {total}\n"
            f"Согласовано: {agreed}\n"
            f"Отказ: {refused}\n"
            f"Повторный визит: {revisit}\n"
            f"Без статуса: {missing}"
        )

        await update.message.reply_text(
            message,
            reply_markup=get_main_keyboard(),
        )
        return

    await update.message.reply_text(
        "Выбери кнопку.",
        reply_markup=get_main_keyboard(),
    )
