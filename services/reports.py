from telegram.error import TelegramError

from config import GROUP_CHAT_ID
from utils.logger import logger


async def send_group_report(
    context,
    user_name: str,
    pharmacy_code: str,
    address: str,
    status: str,
    comment: str = "",
    stand_format: str | None = None,
):
    logger.info("GROUP_CHAT_ID=%s", GROUP_CHAT_ID)

    if not GROUP_CHAT_ID:
        logger.warning("GROUP_CHAT_ID не задан. Отчёт в группу не отправлен.")
        return

    text = (
        f"📍 Аптека: {pharmacy_code}\n"
        f"🏠 Адрес: {address}\n"
        f"👤 Ответственный: {user_name}\n"
        f"📌 Статус: {status}\n"
    )

    if stand_format:
        text += f"🧩 Формат стенда: {stand_format}\n"

    if comment:
        text += f"💬 Комментарий: {comment}"

    try:
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=text,
        )
    except TelegramError as e:
        logger.exception("Не удалось отправить отчёт в группу: %s", e)
