from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Создать вишлист", callback_data="create_wishlist")],
        [InlineKeyboardButton("📋 Мои вишлисты", callback_data="list_wishlists")],
        [InlineKeyboardButton("⭐ Премиум", callback_data="premium")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")],
    ])


def wishlist_menu(wishlist_id: int, is_owner: bool = True):
    buttons = [
        [InlineKeyboardButton("➕ Добавить желание", callback_data=f"add_item_{wishlist_id}")],
        [InlineKeyboardButton("📤 Поделиться", callback_data=f"share_{wishlist_id}")],
        [InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_wishlist_{wishlist_id}")],
    ]
    if is_owner:
        buttons.append([InlineKeyboardButton("🗑 Удалить вишлист", callback_data=f"delete_wishlist_{wishlist_id}")])
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_lists")])
    return InlineKeyboardMarkup(buttons)


def wishlists_list(wishlists: list, page: int = 0, total: int = 0):
    buttons = []
    for w in wishlists:
        buttons.append([InlineKeyboardButton(f"📋 {w.title}", callback_data=f"view_wishlist_{w.id}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"wishlists_page_{page - 1}"))
    if total > (page + 1) * 8:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"wishlists_page_{page + 1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("➕ Новый вишлист", callback_data="create_wishlist")])
    buttons.append([InlineKeyboardButton("🏠 Главная", callback_data="start")])
    return InlineKeyboardMarkup(buttons)


def occasions_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎂 День рождения", callback_data="occasion_birthday")],
        [InlineKeyboardButton("💍 Свадьба", callback_data="occasion_wedding")],
        [InlineKeyboardButton("🎄 Новый год", callback_data="occasion_new_year")],
        [InlineKeyboardButton("🏠 Дом / переезд", callback_data="occasion_housewarming")],
        [InlineKeyboardButton("👶 Рождение ребёнка", callback_data="occasion_baby")],
        [InlineKeyboardButton("🎯 Без повода", callback_data="occasion_other")],
    ])


def item_priority_keyboard(wishlist_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐️⭐️⭐️⭐️⭐️ Очень хочу!", callback_data=f"priority_5_{wishlist_id}")],
        [InlineKeyboardButton("⭐️⭐️⭐️⭐️ Сильно хочу", callback_data=f"priority_4_{wishlist_id}")],
        [InlineKeyboardButton("⭐️⭐️⭐️ Хорошо бы", callback_data=f"priority_3_{wishlist_id}")],
        [InlineKeyboardButton("⭐️⭐️ Было бы неплохо", callback_data=f"priority_2_{wishlist_id}")],
        [InlineKeyboardButton("⭐️ Не обязательно", callback_data=f"priority_1_{wishlist_id}")],
    ])


def item_menu(item_id: int, is_reserved: bool):
    buttons = []
    if not is_reserved:
        buttons.append([InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_item_{item_id}")])
        buttons.append([InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_item_{item_id}")])
    buttons.append([InlineKeyboardButton("◀️ Назад к вишлисту", callback_data=f"back_to_item_{item_id}")])
    return InlineKeyboardMarkup(buttons)


def premium_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📆 249 ₽ / месяц", callback_data="pay_month")],
        [InlineKeyboardButton("🎉 1 499 ₽ / год (-50%)", callback_data="pay_year")],
        [InlineKeyboardButton("◀️ Назад", callback_data="start")],
    ])


def shared_wishlist_actions(wishlist_id: int, share_code: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Копировать ссылку", callback_data=f"copy_link_{share_code}")],
        [InlineKeyboardButton("📱 Открыть в браузере", url=f"https://t.me/...")],
    ])


def confirm_delete_keyboard(wishlist_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{wishlist_id}"),
            InlineKeyboardButton("❌ Нет", callback_data=f"view_wishlist_{wishlist_id}"),
        ]
    ])
