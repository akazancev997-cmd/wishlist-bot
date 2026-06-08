"""Запуск бота в режиме polling."""
import logging
import os
import sys

from dotenv import load_dotenv
load_dotenv()

from telegram.ext import Application
from bot import setup_handlers
from database import init_db

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def post_init(app):
    await init_db()
    logger.info("Database initialized")


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN not set!")
        sys.exit(1)
    
    app = Application.builder().token(token).post_init(post_init).build()
    setup_handlers(app)
    logger.info("Bot started in polling mode")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
