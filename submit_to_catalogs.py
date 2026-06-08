#!/usr/bin/env python3
"""Автоматическая подача бота в каталоги Telegram-ботов.

Запусти: python3 submit_to_catalogs.py
Скрипт откроет страницы подачи в браузере — заполни форму и отправь.
"""

import webbrowser
import subprocess
import sys
import os

BOT_USERNAME = "rtfyhjkuyhtrgerf_bot"
BOT_NAME = "WishlistBot"
BOT_URL = f"https://t.me/{BOT_USERNAME}"
SITE_URL = "https://wishlist-bot.onrender.com"

CATALOGS = [
    {
        "name": "Telegram Bot List (storebot.me)",
        "url": "https://storebot.me/bots/submit",
        "note": "Заполни форму: username, описание, категория Lifestyle",
    },
    {
        "name": "BotList.org",
        "url": "https://botlist.org/bots/new",
        "note": "Добавь бота: название, описание на английском, категория",
    },
    {
        "name": "Telegram Bots (tlgrm.ru)",
        "url": "https://tlgrm.ru/bots/add",
        "note": "Форма на русском. Укажи username и описание",
    },
    {
        "name": "Bots.house",
        "url": "https://bots.house/add-bot",
        "note": "Простая форма: username, название, описание",
    },
    {
        "name": "TelegramBot (telegram-bot.ru)",
        "url": "https://telegram-bot.ru/add/",
        "note": "Каталог русских ботов. Заполни форму.",
    },
    {
        "name": "BotDB (botdb.org)",
        "url": "https://botdb.org/submit",
        "note": "Международный каталог. Английский язык.",
    },
    {
        "name": "@BotList (Telegram)",
        "url": f"tg://resolve?domain=BotList",
        "note": f"Открой Telegram → найди @BotList → отправь: {BOT_USERNAME}",
    },
    {
        "name": "Telegram Channels (tgchannels.org)",
        "url": "https://tgchannels.org/add-bot/",
        "note": "Можно добавить и канал, и бота",
    },
]

SOCIAL_PLATFORMS = [
    {
        "name": "Pikabu — «Я сделал это»",
        "url": "https://pikabu.ru/new",
        "note": "Опубликуй историю создания бота в сообществе «Я сделал это». Авторские посты хорошо вирусятся.",
    },
    {
        "name": "VC.ru — Стартапы",
        "url": "https://vc.ru/new",
        "note": "Напиши статью в стиле «Как я сделал Telegram-бота и что из этого вышло». Аудитория VC любит такие истории.",
    },
    {
        "name": "Habr — Pet-проекты",
        "url": "https://habr.com/ru/hub/pet_projects/",
        "note": "Хабр — лучшая площадка для IT-историй. Опубликуй статью про разработку бота.",
    },
    {
        "name": "TJournal",
        "url": "https://tjournal.ru/new",
        "note": "Молодёжная аудитория. История про полезного бота зайдёт.",
    },
]

FORUMS = [
    {
        "name": "4pda.to — Программы для Android",
        "url": "https://4pda.to/forum/index.php?showforum=72",
        "note": "Огромный форум. Создай тему в разделе «Программы». Приложи описание бота.",
    },
    {
        "name": "NGR (next-ger.ru) — Софт",
        "url": "https://next-ger.ru/forum/",
        "note": "Форум где делятся полезными программами и сервисами.",
    },
    {
        "name": "CyberForum.ru — Telegram",
        "url": "https://www.cyberforum.ru/telegram/",
        "note": "Раздел про Telegram на крупном IT-форуме. Создай тему.",
    },
]

SEO_DIRECTORIES = [
    {
        "name": "DProfile (Хабр Карьера)",
        "url": "https://career.habr.com/",
        "note": "Создай профиль специалиста и добавь проект в портфолио.",
    },
    {
        "name": "GitHub README",
        "url": "https://github.com/akazancev997-cmd/wishlist-bot",
        "note": "Репозиторий уже есть. Поставь звезду и добавь описание проекта.",
    },
    {
        "name": "Google My Business",
        "url": "https://www.google.com/business/",
        "note": "Можно создать профиль компании и указать сайт с ботом.",
    },
]


def open_urls(urls, title):
    input(f"\n⏸ Нажми Enter, чтобы открыть {title} в браузере...")
    for item in urls:
        print(f"\n   🔗 {item['name']}: {item['url']}")
        print(f"   💡 {item['note']}")
        webbrowser.open(item["url"])


def print_article_templates():
    print("""
📝 ГОТОВЫЙ ТЕКСТ ДЛЯ СТАТЬИ НА PIKABU / VC.RU / HABR
========================================================

Заголовок: «Сделал Telegram-бота для вишлистов — теперь никто не дарит носки»

Текст:
-------
Год назад я получил на день рождения 3 кружки, 2 халата и набор носков.
Из 15 подарков реально обрадовал только 1.

Я решил эту проблему — сделал Telegram-бота.

WishlistBot позволяет:
— Создать список желаний за 1 минуту
— Добавить цены и ссылки на товары
— Поделиться ссылкой с друзьями
— Друзья резервируют подарки (ты не видишь кто что выбрал)

Всё работает через Telegram и даже без него (веб-версия).

Результат: 
— 0 ненужных подарков
— Друзья довольны, что не пришлось мучительно выбирать
— Я получил то, что реально хотел

Бот бесплатный, есть премиум (249р/мес) для безлимита.

👉 https://t.me/rtfyhjkuyhtrgerf_bot

Буду рад фидбегу и идеям!
""")


def main():
    print("=" * 60)
    print("🚀 WISHLISTBOT — АВТОМАТИЧЕСКАЯ ПОДАЧА В КАТАЛОГИ")
    print("=" * 60)
    print(f"Бот: @{BOT_USERNAME}")
    print(f"Сайт: {SITE_URL}")
    print()

    print("1️⃣  Каталоги Telegram-ботов (8 шт)")
    print("2️⃣  Социальные платформы (4 шт)")
    print("3️⃣  Форумы (3 шт)")
    print("4️⃣  SEO-директории (3 шт)")
    print("5️⃣  Показать готовый текст для статьи")
    print("6️⃣  Открыть ВСЁ сразу")
    print("q — Выход")

    choice = input("\nВыбери действие: ").strip()

    if choice == "1":
        open_urls(CATALOGS, "каталоги ботов")
    elif choice == "2":
        open_urls(SOCIAL_PLATFORMS, "соцплатформы")
    elif choice == "3":
        open_urls(FORUMS, "форумы")
    elif choice == "4":
        open_urls(SEO_DIRECTORIES, "SEO-директории")
    elif choice == "5":
        print_article_templates()
    elif choice == "6":
        open_urls(CATALOGS + SOCIAL_PLATFORMS + FORUMS + SEO_DIRECTORIES, "ВСЁ")
    elif choice == "q":
        return
    else:
        print("Неверный выбор")

    main()


if __name__ == "__main__":
    main()
