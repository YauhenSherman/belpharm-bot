from telegram.ext import ContextTypes

from config import GROUP_CHAT_ID


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