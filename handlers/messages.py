from telegram import Update
from telegram.ext import ContextTypes

from config import USER_MAP
from keyboards.reply import (
    get_main_keyboard,
    build_codes_keyboard,
    build_districts_keyboard,
    get_stand_format_keyboard,
    get_free_pharmacy_keyboard,
    get_locked_by_me_keyboard,
    get_readonly_pharmacy_keyboard,
)
from services.sheets import (
    get_rows,
    assign_pharmacy,
    unassign_pharmacy,
    finalize_pharmacy,
)
from services.reports import send_group_report
from services.pharmacy import (
    get_user_name,
    build_pharmacy_card,
    find_row_by_label,
    find_row_by_uid,
    FINAL_STATUSES,
    FREE_STATE,
    LOCKED_STATE,
    DONE_STATE,
    get_pharmacy_state,
    is_locked_by_user,
    get_row_responsible,
)
from state.memory import (
    user_state,
    selected_pharmacy_uid,
    selected_pharmacy_label,
    pending_status,
    pending_stand_format,
    pending_comment,
    selected_district,
)
from utils.logger import logger


STAND_FORMATS = [
    "А4 вертикаль",
    "А4 горизонт",
    "А5",
    "А6 наклейка",
]


def get_actions_keyboard(row: dict, current_user_name: str):
    pharmacy_state = get_pharmacy_state(row)
    if pharmacy_state == FREE_STATE:
        return get_free_pharmacy_keyboard()
    if pharmacy_state == LOCKED_STATE and is_locked_by_user(row, current_user_name):
        return get_locked_by_me_keyboard()
    return get_readonly_pharmacy_keyboard()


async def save_final_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    telegram_id: int,
    current_user_name: str,
    selected_row: dict,
    status: str,
    stand_format: str | None = None,
):
    comment = pending_comment.get(telegram_id, "")

    saved_row = finalize_pharmacy(
        uid=str(selected_row.get("UID", "")),
        status=status,
        stand_format=stand_format,
    )

    await send_group_report(
        context=context,
        user_name=current_user_name,
        pharmacy_code=str(saved_row.get("КОД", "")),
        address=str(saved_row.get("Адрес", "")),
        status=status,
        comment=comment,
        stand_format=stand_format,
    )

    user_state.pop(telegram_id, None)
    pending_status.pop(telegram_id, None)
    pending_stand_format.pop(telegram_id, None)
    pending_comment.pop(telegram_id, None)

    saved_message = f"Сохранено ✅\n\nСтатус: {status}"
    if stand_format:
        saved_message += f"\nФормат: {stand_format}"
    if comment:
        saved_message += f"\nКомментарий: {comment}"

    await update.message.reply_text(
        saved_message,
        reply_markup=get_main_keyboard(),
    )


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
        pending_comment.pop(telegram_id, None)
        selected_pharmacy_uid.pop(telegram_id, None)
        selected_pharmacy_label.pop(telegram_id, None)
        selected_district.pop(telegram_id, None)

        await update.message.reply_text(
            "Главное меню 👇",
            reply_markup=get_main_keyboard(),
        )
        return

    rows = get_rows()
    current_user_name = get_user_name(telegram_id, USER_MAP)
    selected_uid = selected_pharmacy_uid.get(telegram_id)
    selected_row = find_row_by_uid(rows, selected_uid) if selected_uid else None

    if user_state.get(telegram_id) == "waiting_stand_format":
        if text == "Отмена":
            user_state.pop(telegram_id, None)
            pending_status.pop(telegram_id, None)
            pending_stand_format.pop(telegram_id, None)
            await update.message.reply_text(
                "Выбор формата отменён.",
                reply_markup=get_main_keyboard(),
            )
            return

        if text not in STAND_FORMATS:
            await update.message.reply_text(
                "Выбери формат стенда кнопкой ниже.",
                reply_markup=get_stand_format_keyboard(),
            )
            return

        if not selected_row or not is_locked_by_user(selected_row, current_user_name):
            await update.message.reply_text(
                "Эта аптека уже не закреплена за тобой.",
                reply_markup=get_main_keyboard(),
            )
            return

        await save_final_status(
            update=update,
            context=context,
            telegram_id=telegram_id,
            current_user_name=current_user_name,
            selected_row=selected_row,
            status="Согласовано",
            stand_format=text,
        )
        return

    if text == "Комментарий":
        if not selected_row:
            await update.message.reply_text(
                "Сначала выбери аптеку.",
                reply_markup=get_main_keyboard(),
            )
            return

        if not is_locked_by_user(selected_row, current_user_name):
            await update.message.reply_text(
                "Комментарий можно оставить только для своей закреплённой аптеки.",
                reply_markup=get_actions_keyboard(selected_row, current_user_name),
            )
            return

        user_state[telegram_id] = "waiting_comment"
        await update.message.reply_text(
            "Напиши комментарий текстом.\n\nИли нажми «Меню» для отмены.",
            reply_markup=get_main_keyboard(),
        )
        return

    if user_state.get(telegram_id) == "waiting_comment":
        if not selected_row or not is_locked_by_user(selected_row, current_user_name):
            user_state.pop(telegram_id, None)
            await update.message.reply_text(
                "Эта аптека уже не закреплена за тобой.",
                reply_markup=get_main_keyboard(),
            )
            return

        pending_comment[telegram_id] = text
        user_state.pop(telegram_id, None)

        await update.message.reply_text(
            f"Комментарий сохранён:\n\n{text}",
            reply_markup=get_locked_by_me_keyboard(),
        )
        return

    if text == "Закрепить за мной":
        if not selected_row:
            await update.message.reply_text(
                "Сначала выбери аптеку.",
                reply_markup=get_main_keyboard(),
            )
            return

        if get_pharmacy_state(selected_row) != FREE_STATE:
            await update.message.reply_text(
                "Эта аптека уже не свободна.",
                reply_markup=get_actions_keyboard(selected_row, current_user_name),
            )
            return

        saved_row = assign_pharmacy(str(selected_row.get("UID", "")), current_user_name)
        selected_pharmacy_uid[telegram_id] = saved_row.get("UID")
        selected_pharmacy_label[telegram_id] = saved_row.get("LABEL")

        await update.message.reply_text(
            "Аптека закреплена за тобой ✅",
            reply_markup=get_main_keyboard(),
        )
        await update.message.reply_text(
            build_pharmacy_card(saved_row),
            reply_markup=get_locked_by_me_keyboard(),
        )
        return

    if text == "Снять закрепление":
        if not selected_row:
            await update.message.reply_text(
                "Сначала выбери аптеку.",
                reply_markup=get_main_keyboard(),
            )
            return

        if not is_locked_by_user(selected_row, current_user_name):
            await update.message.reply_text(
                "Можно снять только свою закреплённую аптеку со статусом «Закреплена».",
                reply_markup=get_actions_keyboard(selected_row, current_user_name),
            )
            return

        unassigned = unassign_pharmacy(str(selected_row.get("UID", "")))
        selected_pharmacy_uid[telegram_id] = unassigned.get("UID")
        selected_pharmacy_label[telegram_id] = unassigned.get("LABEL")
        pending_status.pop(telegram_id, None)
        pending_stand_format.pop(telegram_id, None)
        pending_comment.pop(telegram_id, None)
        user_state.pop(telegram_id, None)

        await update.message.reply_text(
            "Закрепление снято.",
            reply_markup=get_main_keyboard(),
        )
        await update.message.reply_text(
            build_pharmacy_card(unassigned),
            reply_markup=get_free_pharmacy_keyboard(),
        )
        return

    if text in FINAL_STATUSES:
        if not selected_row:
            await update.message.reply_text(
                "Сначала выбери аптеку.",
                reply_markup=get_main_keyboard(),
            )
            return

        if not is_locked_by_user(selected_row, current_user_name):
            await update.message.reply_text(
                "Финальный статус можно ставить только своей закреплённой аптеке.",
                reply_markup=get_actions_keyboard(selected_row, current_user_name),
            )
            return

        if text == "Согласовано":
            user_state[telegram_id] = "waiting_stand_format"
            pending_status[telegram_id] = text
            await update.message.reply_text(
                "Выбери формат стенда 👇",
                reply_markup=get_stand_format_keyboard(),
            )
            return

        await save_final_status(
            update=update,
            context=context,
            telegram_id=telegram_id,
            current_user_name=current_user_name,
            selected_row=selected_row,
            status=text,
            stand_format=None,
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

        pharmacy_state = get_pharmacy_state(found_row)
        is_owner = is_locked_by_user(found_row, current_user_name)
        actions_keyboard = get_actions_keyboard(found_row, current_user_name)

        logger.info(
            "SELECT_PHARMACY | user=%s | uid=%s | label=%s | step=%s | "
            "current_user_name=%s | responsible=%s | status=%s | pharmacy_state=%s | is_owner=%s | "
            "keyboard_type=%s | keyboard=%s",
            telegram_id,
            selected_pharmacy_uid.get(telegram_id),
            selected_pharmacy_label.get(telegram_id),
            user_state.get(telegram_id),
            current_user_name,
            get_row_responsible(found_row),
            found_row.get("Результаты согласования", found_row.get("Статус", "")),
            pharmacy_state,
            is_owner,
            type(actions_keyboard).__name__,
            getattr(actions_keyboard, "keyboard", None),
        )

        await update.message.reply_text(
            build_pharmacy_card(found_row),
            reply_markup=actions_keyboard,
        )
        return

    if text == "Мои аптеки":
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
            responsible = get_row_responsible(row)
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
        free_rows = [row for row in rows if get_pharmacy_state(row) == FREE_STATE]

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
        locked = 0
        completed = 0
        free = 0

        for row in rows:
            state = get_pharmacy_state(row)
            if state == FREE_STATE:
                free += 1
            elif state == LOCKED_STATE:
                locked += 1
            elif state == DONE_STATE:
                completed += 1

        message = (
            "📊 Статистика\n\n"
            f"Всего аптек: {total}\n"
            f"Свободные: {free}\n"
            f"Закреплённые: {locked}\n"
            f"Завершённые: {completed}"
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