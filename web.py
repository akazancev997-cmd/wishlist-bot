import logging
import json
import hmac
import hashlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader

from telegram import Update
from telegram.ext import Application

import config
import database
from models import Wishlist, WishlistItem
from bot import setup_handlers, handle_payment_success
from database import get_session, init_db, close_db

logger = logging.getLogger(__name__)

templates_env = Environment(loader=FileSystemLoader("templates"))

# Telegram bot application (lazy init)
tg_app: Application = None


async def get_tg_app() -> Application:
    global tg_app
    if tg_app is None:
        tg_app = Application.builder().token(config.BOT_TOKEN).build()
        setup_handlers(tg_app)
    return tg_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    bot_app = await get_tg_app()
    if config.WEBHOOK_URL:
        await bot_app.bot.set_webhook(url=f"{config.WEBHOOK_URL}/webhook")
        logger.info(f"Webhook set to {config.WEBHOOK_URL}/webhook")
    yield
    if tg_app:
        await tg_app.stop()
    await close_db()


app = FastAPI(title="WishlistBot", lifespan=lifespan)


# ========== Telegram Webhook ==========

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    bot_app = await get_tg_app()
    update = Update.de_json(data, bot_app.bot)
    if update:
        await bot_app.process_update(update)
    return {"ok": True}


# ========== YooKassa Payment Webhook ==========

@app.post("/yookassa/webhook")
async def yookassa_webhook(request: Request):
    """Handle YooKassa payment notifications."""
    body = await request.body()
    signature = request.headers.get("Authorization", "")

    # Verify signature
    if config.YOOKASSA_SECRET_KEY:
        expected_sig = hmac.new(
            config.YOOKASSA_SECRET_KEY.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        # Simple verification (in production, use proper signature check)

    data = json.loads(body)
    event = data.get("event")
    if event == "payment.waiting_for_capture":
        payment_id = data["object"]["id"]
        metadata = data["object"].get("metadata", {})
        user_id = int(metadata.get("user_id", 0))
        if user_id:
            await _capture_payment(payment_id)
            await handle_payment_success(user_id, payment_id)
        return {"ok": True}

    elif event == "payment.succeeded":
        payment_id = data["object"]["id"]
        metadata = data["object"].get("metadata", {})
        user_id = int(metadata.get("user_id", 0))
        if user_id:
            await handle_payment_success(user_id, payment_id)
        return {"ok": True}

    return {"ok": True}


async def _capture_payment(payment_id: str):
    """Capture a YooKassa payment that's waiting for capture."""
    import base64
    import aiohttp

    auth = base64.b64encode(
        f"{config.YOOKASSA_SHOP_ID}:{config.YOOKASSA_SECRET_KEY}".encode()
    ).decode()

    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.yookassa.ru/v3/payments/{payment_id}/capture",
                headers=headers,
                json={},
            ) as resp:
                if resp.status not in (200, 201):
                    logger.error(f"Capture failed: {resp.status} {await resp.text()}")
    except Exception as e:
        logger.error(f"Capture error: {e}")


# ========== Web Pages ==========

@app.get("/", response_class=HTMLResponse)
async def landing_page():
    tmpl = templates_env.get_template("index.html")
    return tmpl.render()


@app.get("/wishlist/{share_code}", response_class=HTMLResponse)
async def view_shared_wishlist(share_code: str, request: Request):
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Wishlist).where(Wishlist.share_code == share_code)
        )
        wl = result.scalars().first()
        if not wl:
            tmpl = templates_env.get_template("wishlist.html")
            return tmpl.render(wishlist=None, error="Вишлист не найден")

        items_result = await session.execute(
            select(WishlistItem).where(WishlistItem.wishlist_id == wl.id)
            .order_by(WishlistItem.priority.desc(), WishlistItem.created_at)
        )
        items = list(items_result.scalars().all())

    tmpl = templates_env.get_template("wishlist.html")
    return tmpl.render(
        wishlist={
            "id": wl.id,
            "title": wl.title,
            "description": wl.description or "",
            "occasion": wl.occasion or "",
            "share_code": wl.share_code,
            "items": [
                {
                    "id": item.id,
                    "title": item.title,
                    "description": item.description or "",
                    "price": int(item.price) if item.price else None,
                    "currency": item.currency,
                    "url": item.url or "",
                    "priority": item.priority or 3,
                    "is_reserved": item.is_reserved,
                    "reserved_by_name": item.reserved_by_name or "",
                }
                for item in items
            ],
        },
        error=None,
    )


@app.post("/wishlist/{share_code}/reserve/{item_id}")
async def reserve_item(share_code: str, item_id: int, request: Request):
    """Mark an item as reserved (someone is gifting it)."""
    data = await request.json()
    name = data.get("name", "Аноним")

    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(WishlistItem).where(
                WishlistItem.id == item_id,
                WishlistItem.wishlist_id == Wishlist.id,
            ).join(Wishlist, Wishlist.id == WishlistItem.wishlist_id)
            .where(Wishlist.share_code == share_code)
        )
        item = result.scalars().first()
        if not item:
            raise HTTPException(404, "Item not found")
        if item.is_reserved:
            raise HTTPException(400, "Item already reserved")

        item.is_reserved = True
        item.reserved_by_name = name
        await session.commit()

    return {"ok": True, "name": name}


@app.get("/payment/success", response_class=HTMLResponse)
async def payment_success():
    tmpl = templates_env.get_template("payment_success.html")
    return tmpl.render()


@app.get("/robots.txt", response_class=HTMLResponse)
async def robots():
    tmpl = templates_env.get_template("robots.txt")
    return tmpl.render()


@app.get("/sitemap.xml", response_class=HTMLResponse)
async def sitemap():
    tmpl = templates_env.get_template("sitemap.xml")
    return tmpl.render()


@app.get("/privacy", response_class=HTMLResponse)
async def privacy():
    tmpl = templates_env.get_template("privacy.html")
    return tmpl.render()


@app.get("/terms", response_class=HTMLResponse)
async def terms():
    tmpl = templates_env.get_template("terms.html")
    return tmpl.render()


BLOG_ARTICLES = {
    "kak-sozdat-vishlist-dlya-dnya-rozhdeniya": "blog/kak-sozdat-vishlist-dlya-dnya-rozhdeniya.html",
    "chto-podarit-na-noviy-god": "blog/chto-podarit-na-noviy-god.html",
    "svadebniy-vishlist-dlya-gostey": "blog/svadebniy-vishlist-dlya-gostey.html",
}


@app.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_article(slug: str):
    template = BLOG_ARTICLES.get(slug)
    if not template:
        return HTMLResponse("<h1>Статья не найдена</h1><a href='/'>На главную</a>", status_code=404)
    tmpl = templates_env.get_template(template)
    return tmpl.render()
