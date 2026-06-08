import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

import config
import messages
import keyboards
from database import get_session
from models import User, Wishlist, WishlistItem, Subscription, SubscriptionStatus

logger = logging.getLogger(__name__)

# Conversation states
TITLE, DESCRIPTION, OCCASION, ITEM_TITLE, ITEM_DESC, ITEM_PRICE, ITEM_URL = range(7)
EDIT_TITLE, EDIT_DESC = range(7, 9)


async def _get_or_create_user(telegram_id: int, **kwargs) -> User:
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalars().first()
        if user:
            for k, v in kwargs.items():
                setattr(user, k, v)
            await session.commit()
            await session.refresh(user)
            return user
        user = User(telegram_id=telegram_id, **kwargs)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def _get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalars().first()


async def _get_user_wishlists(telegram_id: int) -> list:
    user = await _get_user_by_telegram_id(telegram_id)
    if not user:
        return []
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Wishlist).where(Wishlist.user_id == user.id).order_by(Wishlist.updated_at.desc())
        )
        return list(result.scalars().all())


async def _count_wishlists(telegram_id: int) -> int:
    user = await _get_user_by_telegram_id(telegram_id)
    if not user:
        return 0
    async with get_session() as session:
        from sqlalchemy import select, func
        result = await session.execute(
            select(func.count()).select_from(Wishlist).where(Wishlist.user_id == user.id)
        )
        return result.scalar() or 0


async def _count_items(wishlist_id: int) -> int:
    async with get_session() as session:
        from sqlalchemy import select, func
        result = await session.execute(
            select(func.count()).select_from(WishlistItem).where(WishlistItem.wishlist_id == wishlist_id)
        )
        return result.scalar() or 0


async def _user_is_premium(telegram_id: int) -> bool:
    user = await _get_user_by_telegram_id(telegram_id)
    if not user or not user.is_premium:
        return False
    if user.premium_until and user.premium_until < datetime.now(timezone.utc):
        async with get_session() as session:
            db_user = await session.get(User, user.id)
            if db_user:
                db_user.is_premium = False
                await session.commit()
        return False
    return True


def _get_item_display(item: WishlistItem) -> str:
    price_str = f" — {int(item.price)} {item.currency}" if item.price else ""
    priority_str = "⭐" * (item.priority or 3)
    reserved = " 🔒" if item.is_reserved else ""
    return f"{priority_str} {item.title}{price_str}{reserved}"


# ========== COMMAND HANDLERS ==========

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await _get_or_create_user(
        user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    await update.message.reply_text(
        messages.START,
        reply_markup=keyboards.main_menu(),
        parse_mode="HTML",
    )


async def help_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(messages.HELP, parse_mode="HTML")


async def premium(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await _user_is_premium(user_id):
        user = await _get_user_by_telegram_id(user_id)
        date_str = user.premium_until.strftime("%d.%m.%Y") if user.premium_until else "навсегда"
        text = f"⭐ У тебя уже есть Премиум до {date_str}!"
    else:
        text = messages.PREMIUM_INFO

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML")
        if not await _user_is_premium(user_id):
            await update.callback_query.edit_message_reply_markup(keyboards.premium_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=keyboards.premium_keyboard() if not await _user_is_premium(user_id) else None, parse_mode="HTML")


# ========== WISHLIST CRUD ==========

async def create_wishlist_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_premium = await _user_is_premium(user_id)

    if not is_premium:
        count = await _count_wishlists(user_id)
        if count >= 1:
            await update.effective_message.reply_text(
                "❌ В бесплатном тарифе можно создать только 1 вишлист.\n"
                "Оформи Премиум для безлимита: /premium",
                parse_mode="HTML",
            )
            return ConversationHandler.END

    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("🎁 <b>Создаём вишлист!</b>\n\nПридумай название:", parse_mode="HTML")
    else:
        await update.message.reply_text("🎁 <b>Создаём вишлист!</b>\n\nПридумай название:", parse_mode="HTML")
    return TITLE


async def create_wishlist_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    if len(title) > 256:
        await update.message.reply_text("Название слишком длинное (макс 256 символов). Попробуй короче:")
        return TITLE
    ctx.user_data["wishlist_title"] = title
    await update.message.reply_text(
        "Отлично! Теперь выбери повод:",
        reply_markup=keyboards.occasions_keyboard(),
    )
    return OCCASION


async def create_wishlist_occasion(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    occasion_map = {
        "occasion_birthday": "🎂 День рождения",
        "occasion_wedding": "💍 Свадьба",
        "occasion_new_year": "🎄 Новый год",
        "occasion_housewarming": "🏠 Новоселье",
        "occasion_baby": "👶 Рождение",
        "occasion_other": "🎯 Без повода",
    }
    occasion = occasion_map.get(query.data, "🎯 Без повода")
    ctx.user_data["wishlist_occasion"] = occasion

    title = ctx.user_data["wishlist_title"]
    async with get_session() as session:
        user = await session.get(User, update.effective_user.id)
        if not user:
            user = User(telegram_id=update.effective_user.id)
            session.add(user)
            await session.flush()
        wl = Wishlist(
            user_id=user.id,
            title=title,
            occasion=occasion,
        )
        session.add(wl)
        await session.commit()
        await session.refresh(wl)

    await query.edit_message_text(
        f"✅ <b>Вишлист «{title}» создан!</b>\n\n"
        f"Повод: {occasion}\n\n"
        f"Теперь добавь желания через меню:",
        reply_markup=keyboards.wishlist_menu(wl.id),
        parse_mode="HTML",
    )
    ctx.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END


async def list_wishlists(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    wishlists = await _get_user_wishlists(user_id)

    if not wishlists:
        text = "У тебя ещё нет вишлистов. Создай первый!"
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Создать вишлист", callback_data="create_wishlist")],
            [InlineKeyboardButton("🏠 Главная", callback_data="start")],
        ])
    else:
        lines = []
        for i, w in enumerate(wishlists[:8], 1):
            item_count = await _count_items(w.id)
            lines.append(f"{i}. {w.title} ({item_count} шт)")
        text = "📋 <b>Твои вишлисты:</b>\n\n" + "\n".join(lines)
        markup = keyboards.wishlists_list(wishlists[:8], 0, len(wishlists))

    if query:
        await query.answer()
        if query.message.text != text:
            await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=markup, parse_mode="HTML")


async def view_wishlist(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_parts = query.data.split("_")
    wishlist_id = int(data_parts[-1])

    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Wishlist).where(Wishlist.id == wishlist_id)
        )
        wl = result.scalars().first()
        if not wl:
            await query.edit_message_text("Вишлист не найден.")
            return

        items_result = await session.execute(
            select(WishlistItem).where(WishlistItem.wishlist_id == wishlist_id)
            .order_by(WishlistItem.priority.desc(), WishlistItem.created_at)
        )
        items = list(items_result.scalars().all())

    occasion_str = wl.occasion or "Без повода"
    items_text = "\n".join(
        f"{'🔒' if it.is_reserved else '✅'} {_get_item_display(it)}"
        for it in items
    ) if items else "Пока пусто 🤷‍♂️"

    text = (
        f"<b>{wl.title}</b>\n"
        f"Повод: {occasion_str}\n\n"
        f"<b>Желания ({len(items)}):</b>\n{items_text}"
    )

    await query.edit_message_text(text, reply_markup=keyboards.wishlist_menu(wl.id), parse_mode="HTML")


async def add_item_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_parts = query.data.split("_")
    wishlist_id = int(data_parts[-1])
    ctx.user_data["add_item_wishlist_id"] = wishlist_id

    async with get_session() as session:
        from sqlalchemy import select
        wl_result = await session.execute(select(Wishlist).where(Wishlist.id == wishlist_id))
        wl = wl_result.scalars().first()
        if not wl:
            await query.edit_message_text("Вишлист не найден.")
            return

        async with get_session() as user_session:
            user_db = await user_session.get(User, wl.user_id)
        is_premium = await _user_is_premium(user_db.telegram_id if user_db else 0)
        if not is_premium:
            count_result = await session.execute(
                select(WishlistItem).where(WishlistItem.wishlist_id == wishlist_id)
            )
            items_count = len(list(count_result.scalars().all()))
            if items_count >= 10:
                await query.edit_message_text(
                    "❌ В бесплатном тарифе максимум 10 желаний в одном вишлисте.\n"
                    "Оформи Премиум: /premium",
                    parse_mode="HTML",
                )
                return

    await query.edit_message_text(
        "🎯 <b>Добавляем желание!</b>\n\nНапиши, что хочешь получить в подарок:",
        parse_mode="HTML",
    )
    return ITEM_TITLE


async def add_item_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    if len(title) > 256:
        await update.message.reply_text("Слишком длинно (макс 256). Попробуй короче:")
        return ITEM_TITLE
    ctx.user_data["add_item_title"] = title
    await update.message.reply_text(
        "💰 Укажи примерную цену (или отправь «-», если не знаешь):"
    )
    return ITEM_PRICE


async def add_item_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    price_text = update.message.text.strip()
    price = None
    if price_text and price_text != "-":
        price_text_clean = re.sub(r"[^\d.,]", "", price_text).replace(",", ".")
        try:
            price = float(price_text_clean)
        except ValueError:
            await update.message.reply_text("Цена не понятна. Напиши число или «-»:")
            return ITEM_PRICE

    ctx.user_data["add_item_price"] = price

    await update.message.reply_text(
        "🔗 Добавь ссылку на товар (или отправь «-»):"
    )
    return ITEM_URL


async def add_item_url(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    url_text = update.message.text.strip()
    url = url_text if url_text and url_text != "-" else None
    ctx.user_data["add_item_url"] = url

    title = ctx.user_data["add_item_title"]
    price = ctx.user_data["add_item_price"]
    wishlist_id = ctx.user_data["add_item_wishlist_id"]

    async with get_session() as session:
        item = WishlistItem(
            wishlist_id=wishlist_id,
            title=title,
            price=price,
            url=url,
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)

    await update.message.reply_text(
        f"✅ <b>{title}</b> добавлен(а) в вишлист!",
        parse_mode="HTML",
    )
    ctx.user_data.clear()
    return ConversationHandler.END


async def share_wishlist(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_parts = query.data.split("_")
    wishlist_id = int(data_parts[-1])

    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Wishlist).where(Wishlist.id == wishlist_id))
        wl = result.scalars().first()
        if not wl:
            await query.edit_message_text("Вишлист не найден.")
            return

    base_url = config.WEBHOOK_URL or "https://your-domain.com"
    share_url = f"{base_url}/wishlist/{wl.share_code}"

    await query.edit_message_text(
        f"🎁 <b>{wl.title}</b>\n\n"
        f"Ссылка для друзей:\n{share_url}\n\n"
        f"Отправь её кому хочешь! Они увидят список и смогут отметить, что дарят.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data=f"view_wishlist_{wl.id}")],
        ]),
        parse_mode="HTML",
    )


async def delete_wishlist_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_parts = query.data.split("_")
    wishlist_id = int(data_parts[-1])

    await query.edit_message_text(
        "❓ <b>Точно удалить вишлист?</b>\nВсе желания внутри тоже удалятся.",
        reply_markup=keyboards.confirm_delete_keyboard(wishlist_id),
        parse_mode="HTML",
    )


async def delete_wishlist_execute(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_parts = query.data.split("_")
    wishlist_id = int(data_parts[-1])

    async with get_session() as session:
        result = await session.execute(
            Wishlist.__table__.delete().where(Wishlist.id == wishlist_id)
        )
        await session.commit()

    await query.edit_message_text("🗑 Вишлист удалён.", reply_markup=keyboards.main_menu())


async def view_item(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_parts = query.data.split("_")
    item_id = int(data_parts[-1])

    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(WishlistItem).where(WishlistItem.id == item_id))
        item = result.scalars().first()
        if not item:
            await query.edit_message_text("Желание не найдено.")
            return

    text = f"<b>{item.title}</b>\n"
    if item.description:
        text += f"\n{item.description}\n"
    if item.price:
        text += f"\n💰 {int(item.price)} ₽"
    if item.url:
        text += f"\n🔗 {item.url}"
    text += f"\n⭐ Приоритет: {'⭐' * (item.priority or 3)}"
    if item.is_reserved:
        text += "\n\n🔒 <b>Уже зарезервировано</b>"

    await query.edit_message_text(text, reply_markup=keyboards.item_menu(item.id, item.is_reserved), parse_mode="HTML")


async def delete_item(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_parts = query.data.split("_")
    item_id = int(data_parts[-1])

    async with get_session() as session:
        result = await session.execute(
            WishlistItem.__table__.delete().where(WishlistItem.id == item_id)
        )
        await session.commit()

    await query.edit_message_text("🗑 Желание удалено из списка.", reply_markup=keyboards.main_menu())


# ========== PREMIUM / PAYMENTS ==========

async def premium_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    telegram_id = update.effective_user.id
    if await _user_is_premium(telegram_id):
        user = await _get_user_by_telegram_id(telegram_id)
        date_str = user.premium_until.strftime("%d.%m.%Y") if user and user.premium_until else "навсегда"
        await query.edit_message_text(
            f"⭐ Премиум уже активен до {date_str}!",
            parse_mode="HTML",
        )
        return

    if query.data == "pay_month":
        amount = config.PREMIUM_PRICE_MONTH
        period = 1
        label = "месяц"
    elif query.data == "pay_year":
        amount = config.PREMIUM_PRICE_YEAR
        period = 12
        label = "год"
    else:
        return

    # Generate payment link via YooKassa
    payment_url = await _create_payment(telegram_id, amount, period)
    if payment_url:
        await query.edit_message_text(
            f"💳 <b>Оплата Премиум на {label}</b>\n"
            f"Сумма: {amount / 100} ₽\n\n"
            f"Нажми кнопку ниже для оплаты:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💳 Оплатить {amount/100} ₽", url=payment_url)],
                [InlineKeyboardButton("◀️ Назад", callback_data="premium")],
            ]),
            parse_mode="HTML",
        )
    else:
        await query.edit_message_text(
            "😔 Не удалось создать платёж. ЮKassa не настроена.\n"
            "Настрой переменные YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY.",
        )


async def _create_payment(telegram_id: int, amount: int, period_months: int) -> Optional[str]:
    """Create YooKassa payment and return payment URL."""
    if not config.YOOKASSA_SHOP_ID or not config.YOOKASSA_SECRET_KEY:
        logger.warning("ЮKassa не настроена. Пропускаем создание платежа.")
        return None

    user = await _get_user_by_telegram_id(telegram_id)
    if not user:
        return None

    import uuid
    import base64
    import aiohttp

    idempotence_key = uuid.uuid4().hex
    auth = base64.b64encode(
        f"{config.YOOKASSA_SHOP_ID}:{config.YOOKASSA_SECRET_KEY}".encode()
    ).decode()

    webhook_base = config.WEBHOOK_URL
    payload = {
        "amount": {
            "value": f"{amount / 100:.2f}",
            "currency": "RUB",
        },
        "confirmation": {
            "type": "redirect",
            "return_url": f"{webhook_base}/payment/success",
        },
        "capture": True,
        "description": f"Премиум WishlistBot ({period_months} мес)",
        "metadata": {
            "user_id": str(telegram_id),
            "period_months": str(period_months),
        },
    }

    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json",
        "Idempotence-Key": idempotence_key,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.yookassa.ru/v3/payments",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    # Save payment to DB
                    async with get_session() as db_session:
                        sub = Subscription(
                            user_id=user.id,
                            payment_id=data["id"],
                            amount=amount,
                            period_months=period_months,
                            status=SubscriptionStatus.ACTIVE,
                            started_at=datetime.now(timezone.utc),
                            expires_at=datetime.now(timezone.utc) + timedelta(days=30 * period_months),
                        )
                        db_session.add(sub)
                        await db_session.commit()
                    return data["confirmation"]["confirmation_url"]
                else:
                    logger.error(f"YooKassa error: {resp.status} {await resp.text()}")
                    return None
    except Exception as e:
        logger.error(f"YooKassa exception: {e}")
        return None


async def handle_payment_success(telegram_id: int, payment_id: str):
    """Activate premium after successful payment."""
    user = await _get_user_by_telegram_id(telegram_id)
    if not user:
        return

    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Subscription).where(
                Subscription.payment_id == payment_id,
                Subscription.user_id == user.id,
            )
        )
        sub = result.scalars().first()
        if not sub:
            return

        db_user = await session.get(User, user.id)
        now = datetime.now(timezone.utc)
        db_user.is_premium = True
        if db_user.premium_until and db_user.premium_until > now:
            db_user.premium_until = db_user.premium_until + timedelta(days=30 * sub.period_months)
        else:
            db_user.premium_until = now + timedelta(days=30 * sub.period_months)
        sub.status = SubscriptionStatus.ACTIVE
        await session.commit()


# ========== CALLBACK DISPATCHER ==========

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "start":
        await start(update, ctx)
    elif data == "create_wishlist":
        await create_wishlist_start(update, ctx)
    elif data == "list_wishlists":
        await list_wishlists(update, ctx)
    elif data == "premium":
        await premium(update, ctx)
    elif data == "help":
        await query.answer()
        await query.edit_message_text(messages.HELP, parse_mode="HTML")
    elif data.startswith("view_wishlist_"):
        await view_wishlist(update, ctx)
    elif data.startswith("add_item_"):
        await add_item_start(update, ctx)
    elif data.startswith("share_"):
        await share_wishlist(update, ctx)
    elif data.startswith("delete_wishlist_"):
        await delete_wishlist_confirm(update, ctx)
    elif data.startswith("confirm_delete_"):
        await delete_wishlist_execute(update, ctx)
    elif data.startswith("pay_"):
        await premium_callback(update, ctx)
    elif data.startswith("occasion_"):
        await create_wishlist_occasion(update, ctx)
    elif data.startswith("edit_item_") or data.startswith("delete_item_"):
        if data.startswith("delete_item_"):
            await delete_item(update, ctx)
    elif data.startswith("back_to_lists"):
        await list_wishlists(update, ctx)
    elif data.startswith("wishlists_page_"):
        parts = data.split("_")
        page = int(parts[-1])
        user_id = update.effective_user.id
        wishlists = await _get_user_wishlists(user_id)
        start_idx = page * 8
        page_wls = wishlists[start_idx:start_idx + 8]
        if page_wls:
            lines = [f"{i + 1}. {w.title}" for i, w in enumerate(page_wls, start_idx + 1)]
            text = "📋 <b>Твои вишлисты:</b>\n\n" + "\n".join(lines)
            await query.edit_message_text(text, reply_markup=keyboards.wishlists_list(page_wls, page, len(wishlists)), parse_mode="HTML")
    else:
        await query.answer("Неизвестная команда")


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle text messages that don't match active conversation."""
    if update.message and update.message.text:
        text = update.message.text.strip().lower()
        if text in ("/start", "/help", "/lists", "/create", "/premium", "/share"):
            return
        await update.message.reply_text(
            "Используй команды из меню или кнопки ниже.",
            reply_markup=keyboards.main_menu(),
        )


# ========== SETUP ==========

def setup_handlers(app: Application):
    # Conversation for creating wishlist
    create_conv = ConversationHandler(
        entry_points=[
            CommandHandler("create", create_wishlist_start),
            CallbackQueryHandler(create_wishlist_start, pattern="^create_wishlist$"),
        ],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_wishlist_title)],
            OCCASION: [CallbackQueryHandler(create_wishlist_occasion, pattern="^occasion_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    # Conversation for adding item
    add_item_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_item_start, pattern="^add_item_")],
        states={
            ITEM_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_item_title)],
            ITEM_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_item_price)],
            ITEM_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_item_url)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("premium", premium))
    app.add_handler(CommandHandler("lists", list_wishlists))
    app.add_handler(create_conv)
    app.add_handler(add_item_conv)
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
