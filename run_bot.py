"""Запуск бота в режиме polling (без вебхука, для разработки)."""
import logging
import os

from dotenv import load_dotenv
load_dotenv()

from telegram.ext import Application
from bot import setup_handlers
from database import init_db
import asyncio

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def post_init(app):
    await init_db()
    logger.info("Database initialized")


def main():
    app = Application.builder().token(os.getenv("BOT_TOKEN")).post_init(post_init).build()
    setup_handlers(app)
    logger.info("Бот запущен в режиме polling. Нажми Ctrl+C для остановки.")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
