import asyncio

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram.request import HTTPXRequest

from config import BOT_TOKEN
from handlers.start import start
from handlers.messages import handle_message
from utils.logger import logger


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

    logger.info("Бот запущен...")
    import os

PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    webhook_url=WEBHOOK_URL,
)


if __name__ == "__main__":
    main()