#!/usr/bin/env python3
"""Поиск Telegram-каналов и чатов для продвижения WishlistBot.

Использует публичные каталоги и поиск по ключевым словам.

Как использовать:
1. Запусти: python3 find_channels.py
2. Скрипт откроет браузер со списком релевантных каналов
3. Вступай в каналы и публикуй посты

Требуется: браузер (откроется автоматически)
"""

import webbrowser
import json

# Ключевые слова для поиска Telegram-каналов
KEYWORDS = [
    "подарки идеи",
    "вишлист список желаний",
    "день рождения организация",
    "свадьба организация",
    "новый год подарки",
    "подарок мужчине",
    "подарок женщине",
    "подарок ребёнку",
    "что подарить",
    "lifehack подарки",
    "праздник организация",
    "ивент агентство",
]

# Площадки для поиска каналов
SEARCH_URLS = [
    # TGStat - каталог Telegram каналов
    ("TGStat - Подарки", "https://tgstat.ru/search?q={}"),
    # Telemetr - поиск каналов
    ("Telemetr", "https://telemetr.me/search?q={}"),
    # Поиск в самом Telegram (веб)
    ("Telegram Web Search", "https://t.me/s?q={}"),
    # Google поиск Telegram каналов
    ("Google", "https://www.google.com/search?q=telegram+канал+{}"),
    # Яндекс поиск Telegram каналов
    ("Yandex", "https://yandex.ru/search/?text=telegram+канал+{}"),
    # Биржи рекламы в Telegram
    ("Telega.in", "https://telega.in/search?q={}"),
    ("AdGram", "https://adgram.io/search?q={}"),
]

# Площадки для размещения постов (бесплатно)
FREE_PLATFORMS = [
    ("Pikabu - 'Я сделал это'", "https://pikabu.ru/new"),
    ("VC.ru - Стартапы", "https://vc.ru/new"),
    ("Habr - Я пишу бота", "https://habr.com/ru/search/?q=telegram+бот&target_type=posts"),
    ("Хабрахабр - Пет-проекты", "https://habr.com/ru/hub/pet_projects/"),
]

# Конкурентные боты и сервисы (для анализа и вдохновения)
COMPETITORS = [
    "https://t.me/wish_list_bot",
    "https://t.me/wishlist_gift_bot",
    "https://t.me/GifteryBot",
    "https://t.me/WishGiftBot",
]


def main():
    print("=" * 60)
    print("🎁 WishlistBot — Поиск каналов для продвижения")
    print("=" * 60)

    print("\n📌 1. Ключевые слова для поиска:")
    for kw in KEYWORDS:
        print(f"   • {kw}")

    print("\n🌐 2. Открываю браузер с результатами поиска...")
    print("   (выбери 2-3 запроса и открой ссылки)")

    for name, url in SEARCH_URLS[:5]:
        search_url = url.format(KEYWORDS[0].replace(" ", "+"))
        print(f"   🔍 {name}")
        webbrowser.open(search_url)

    print("\n📢 3. Бесплатные площадки для публикации:")
    for name, url in FREE_PLATFORMS:
        print(f"   • {name}: {url}")

    print("\n👀 4. Конкуренты (для анализа):")
    for c in COMPETITORS:
        print(f"   • {c}")

    print("\n" + "=" * 60)
    print("🔥 СТРАТЕГИЯ ПРОДВИЖЕНИЯ:")
    print("=" * 60)
    print("""
1. **Вступи в 10-20 чатов про подарки** → напиши в каждый
   пост «Надоело получать ненужные подарки? Я сделал бота...»

2. **Опубликуй на Pikabu и VC.ru** → истории о том,
   как создавал бота для вишлистов. Такие посты вирусятся.

3. **Telegram Ads** → когда появится бюджет, настрой
   рекламу на аудиторию 25-35 лет, интересы «подарки/праздники».
   Минимальный бюджет: 300 € (~30 000 ₽)

4. **Партнёрства**: свадебные организаторы, event-агентства,
   блогеры-миллионники в TikTok/Reels (CPA-модель: % с продаж)

5. **Вирусный эффект**: встроенная реферальная система даёт
   +7 дней Премиум за каждого друга. Пользователи сами
   приведут новых.

6. **SEO**: лендинг уже оптимизирован. Добавь ссылку на
   бота в соцсетях (ВК, Instagram, TikTok).
""")


if __name__ == "__main__":
    main()
