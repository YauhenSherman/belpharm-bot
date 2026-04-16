import os
import asyncio

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.request import HTTPXRequest

from config import BOT_TOKEN, USER_MAP
from handlers.start import start
from handlers.messages import handle_message
from utils.logger import logger


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = None
    user_name = "Неизвестный"
    text = None

    if isinstance(update, Update) and update.effective_user:
        user_id = update.effective_user.id
        user_name = USER_MAP.get(user_id, "Неизвестный")

    if isinstance(update, Update) and update.effective_message:
        text = update.effective_message.text

    logger.exception(
        "Ошибка | user=%s (%s) | text=%r",
        user_name,
        user_id,
        text,
        exc_info=context.error,
    )

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Что-то пошло не так. Попробуйте ещё раз или нажмите «Меню»."
            )
        except Exception:
            logger.exception("Не удалось отправить пользователю сообщение об ошибке")


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не найден в .env")

    asyncio.set_event_loop(asyncio.new_event_loop())

    request = HTTPXRequest(
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30,
        pool_timeout=30,
    )

    app = ApplicationBuilder().token(BOT_TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    logger.info("Бот запущен...")

    port = int(os.environ.get("PORT", 10000))
    webhook_url = os.environ.get("WEBHOOK_URL")

    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=webhook_url,
    )


if __name__ == "__main__":
    main()