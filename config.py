import os
from dotenv import load_dotenv

load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан! Получите токен у @BotFather")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/wishlist.db")

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
PORT = int(os.getenv("PORT", "8080"))

# ЮKassa (ЮMoney для бизнеса)
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "")

PREMIUM_PRICE_MONTH = 24900  # 249.00 рублей в копейках
PREMIUM_PRICE_YEAR = 149900  # 1499.00 рублей
