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
import shutil
import sys

TOKEN_PATTERN = re.compile(r"^\d+:[A-Za-z0-9_-]{30,}$")
TOKEN_PLACEHOLDER = "your_bot_token_from_botfather"


def _read_env(env_path: str) -> dict:
    values: dict = {}
    if not os.path.exists(env_path):
        return values
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, _, value = stripped.partition("=")
            values[key.strip()] = value.strip()
    return values


def _save_token(env_path: str, token: str) -> None:
    lines: list = []
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            lines = f.readlines()

    new_line = f"TELEGRAM_BOT_TOKEN={token}\n"
    for i, line in enumerate(lines):
        if line.strip().startswith("TELEGRAM_BOT_TOKEN") and "=" in line:
            lines[i] = new_line
            break
    else:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append(new_line)

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def ensure_bot_token() -> None:
    """Ota-ona uchun: .env faylini yaratadi va bot tokenini interaktiv so'raydi."""
    root = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(root, ".env")
    example_path = os.path.join(root, ".env.example")

    if not os.path.exists(env_path) and os.path.exists(example_path):
        shutil.copyfile(example_path, env_path)
        print("📝 .env fayli yaratildi.")

    token = _read_env(env_path).get("TELEGRAM_BOT_TOKEN", "").strip()
    if token and token != TOKEN_PLACEHOLDER and TOKEN_PATTERN.match(token):
        return

    print()
    print("🤖 Telegram bot tokeni kerak.")
    print("   1. Telegramda @BotFather ga /newbot yozing")
    print("   2. Olingan tokenni shu yerga joylashtiring")
    print("   (Namuna: 123456789:AAE...xyz)")
    print()

    for _ in range(3):
        try:
            raw = input("Bot tokeni: ")
        except (EOFError, KeyboardInterrupt):
            print()
            print("⚠️  Token kiritilmadi. .env faylida TELEGRAM_BOT_TOKEN ni to'ldiring.")
            return

        cleaned = re.sub(r"\s+", "", raw)
        if TOKEN_PATTERN.match(cleaned):
            _save_token(env_path, cleaned)
            print("✅ Token saqlandi (.env fayliga).")
            return
        print("❌ Token formati noto'g'ri. Qayta urinib ko'ring.")

    print("⚠️  Token saqlanmadi. Keyinroq .env faylida TELEGRAM_BOT_TOKEN ni to'ldirishingiz mumkin.")


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
        ensure_bot_token()
        print("🤖 Telegram bot ishga tushmoqda...")
        run_bot()
        return

    # Ikkalasi (API + bot) ishga tushishidan oldin token so'ralsin
    ensure_bot_token()

    # Ikkalasini ham ishga tushirish
    print("=" * 50)
    print("🏫 Maktab Turniket Tizimi")
    print("=" * 50)
    print("🚀 API:   http://localhost:8000")
    print("📊 Admin: http://localhost:8000/admin")
    print("📖 Docs:  http://localhost:8000/docs")
    print("=" * 50)

    api_proc = multiprocessing.Process(target=run_api, name="api-server")
    bot_proc = multiprocessing.Process(target=run_bot, name="telegram-bot")

    api_proc.start()
    bot_proc.start()

    try:
        api_proc.join()
        bot_proc.join()
    except KeyboardInterrupt:
        print("\n⏹ To'xtatilmoqda...")
        api_proc.terminate()
        bot_proc.terminate()


if __name__ == "__main__":
    main()
