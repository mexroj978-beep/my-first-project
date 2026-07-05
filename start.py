#!/usr/bin/env python3
"""
Maktab Turniket tizimini ishga tushirish.

Ishlatish:
  python start.py          # API server + Telegram bot
  python start.py --api    # Faqat API server
  python start.py --bot    # Faqat Telegram bot
  python start.py --seed   # Namuna ma'lumotlar yuklash
"""

import argparse
import multiprocessing
import os
import re
import sys

TOKEN_RE = re.compile(r"^\d+:[A-Za-z0-9_-]{30,}$")


def _normalize_token(raw: str) -> str:
    """BotFather tokenidagi ortiqcha bo'sh joy/qator belgilarini olib tashlash."""
    if not raw:
        return ""
    return re.sub(r"\s+", "", raw)


def _write_env_token(root: str, token: str) -> None:
    """.env fayliga TELEGRAM_BOT_TOKEN ni yozish (mavjud bo'lsa yangilash)."""
    env_path = os.path.join(root, ".env")
    example_path = os.path.join(root, ".env.example")

    lines: list[str] = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    elif os.path.exists(example_path):
        with open(example_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

    replaced = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("TELEGRAM_BOT_TOKEN"):
            lines[i] = f"TELEGRAM_BOT_TOKEN={token}"
            replaced = True
            break
    if not replaced:
        lines.insert(0, f"TELEGRAM_BOT_TOKEN={token}")

    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip("\n") + "\n")


def ensure_bot_token(root: str) -> bool:
    """Telegram bot tokeni sozlanganini tekshirish, aks holda so'rab olish.

    Token to'g'ri bo'lsa True qaytaradi. Foydalanuvchi tokenni interaktiv
    kiritsa, uni .env fayliga saqlaydi va joriy jarayon uchun ham o'rnatadi.
    """
    from app.config import settings

    token = _normalize_token(settings.telegram_bot_token)
    if TOKEN_RE.match(token):
        # Foydalanuvchi tasodifan bo'sh joy bilan yozgan bo'lsa, tozalab qo'yamiz.
        if token != settings.telegram_bot_token:
            os.environ["TELEGRAM_BOT_TOKEN"] = token
            settings.telegram_bot_token = token
            _write_env_token(root, token)
        return True

    if not sys.stdin or not sys.stdin.isatty():
        print("=" * 50)
        print("⚠️  TELEGRAM_BOT_TOKEN sozlanmagan!")
        print("   .env faylini oching va tokenni kiriting:")
        print("   TELEGRAM_BOT_TOKEN=123456:AA...")
        print("=" * 50)
        return False

    print("=" * 50)
    print("🤖 Telegram bot tokeni topilmadi.")
    print("   Token @BotFather dan olinadi (/newbot).")
    print("=" * 50)

    for _ in range(3):
        try:
            raw = input("Bot tokenini shu yerga qo'ying va Enter bosing: ")
        except (EOFError, KeyboardInterrupt):
            print("\n⏹ Bekor qilindi.")
            return False

        token = _normalize_token(raw)
        if TOKEN_RE.match(token):
            _write_env_token(root, token)
            os.environ["TELEGRAM_BOT_TOKEN"] = token
            settings.telegram_bot_token = token
            print("✅ Token saqlandi (.env fayliga).")
            return True

        print("❌ Token formati noto'g'ri. Masalan: 123456789:AAF...  Qayta urinib ko'ring.")

    print("⚠️  Token kiritilmadi. Bot ishga tushmaydi.")
    return False


def run_api() -> None:
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)


def run_bot() -> None:
    from app.bot.handlers import run_bot

    run_bot()


def run_seed() -> None:
    import asyncio

    from scripts.seed_data import seed

    asyncio.run(seed())


def main() -> None:
    parser = argparse.ArgumentParser(description="Maktab Turniket + Telegram Bot")
    parser.add_argument("--api", action="store_true", help="Faqat API server")
    parser.add_argument("--bot", action="store_true", help="Faqat Telegram bot")
    parser.add_argument("--seed", action="store_true", help="Namuna ma'lumotlar yuklash")
    args = parser.parse_args()

    root = os.path.dirname(os.path.abspath(__file__))
    if root not in sys.path:
        sys.path.insert(0, root)

    if args.seed:
        run_seed()
        return

    if args.api:
        print("🚀 API server ishga tushmoqda: http://localhost:8000")
        print("📊 Admin panel: http://localhost:8000/admin")
        run_api()
        return

    if args.bot:
        if not ensure_bot_token(root):
            sys.exit(1)
        print("🤖 Telegram bot ishga tushmoqda...")
        run_bot()
        return

    # Ikkalasini ham ishga tushirish. Token subprotsess ochilishidan oldin
    # asosiy jarayonda so'raladi (interaktiv kiritish uchun).
    bot_ready = ensure_bot_token(root)

    print("=" * 50)
    print("🏫 Maktab Turniket Tizimi")
    print("=" * 50)
    print("🚀 API:   http://localhost:8000")
    print("📊 Admin: http://localhost:8000/admin")
    print("📖 Docs:  http://localhost:8000/docs")
    if not bot_ready:
        print("⚠️  Telegram bot O'CHIQ (token yo'q) — faqat API ishlaydi.")
    print("=" * 50)

    api_proc = multiprocessing.Process(target=run_api, name="api-server")
    api_proc.start()

    bot_proc = None
    if bot_ready:
        bot_proc = multiprocessing.Process(target=run_bot, name="telegram-bot")
        bot_proc.start()

    try:
        api_proc.join()
        if bot_proc is not None:
            bot_proc.join()
    except KeyboardInterrupt:
        print("\n⏹ To'xtatilmoqda...")
        api_proc.terminate()
        if bot_proc is not None:
            bot_proc.terminate()


if __name__ == "__main__":
    main()
