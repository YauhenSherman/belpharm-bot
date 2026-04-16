from telegram.ext import ContextTypes

from config import GROUP_CHAT_ID

from utils.logger import logger

async def send_group_report(context, message):
    try:
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=message,
        )
    except Exception:
        logger.exception("Не удалось отправить отчёт в группу")
        raise
    
async def send_group_report(
    context: ContextTypes.DEFAULT_TYPE,
    user_name: str,
    pharmacy_code: str,
    address: str,
    status: str,
    comment: str,
):
    message = (
        f"📝 Новый отчёт\n\n"
        f"👤 {user_name}\n"
        f"🏥 Аптека: {pharmacy_code}\n"
        f"📍 Адрес: {address}\n"
        f"📊 Статус: {status}\n"
        f"💬 Комментарий: {comment}"
    )

    await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=message,
    )
    