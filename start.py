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

ROOT = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(ROOT, ".env")
ENV_EXAMPLE = os.path.join(ROOT, ".env.example")
TOKEN_PLACEHOLDER = "your_bot_token_from_botfather"
TOKEN_PATTERN = re.compile(r"^\d+:[A-Za-z0-9_-]{30,}$")


def _sanitize_token(raw: str) -> str:
    """Nusxalashda tushib qolgan bo'shliq va qo'shtirnoqlarni olib tashlash."""
    return re.sub(r"\s+", "", raw).strip("\"'")


def _read_saved_token() -> str:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if token:
        return token
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("TELEGRAM_BOT_TOKEN="):
                    return line.strip().split("=", 1)[1].strip().strip("\"'")
    return ""


def _save_token(token: str) -> None:
    if not os.path.exists(ENV_FILE) and os.path.exists(ENV_EXAMPLE):
        shutil.copyfile(ENV_EXAMPLE, ENV_FILE)

    lines: list[str] = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, encoding="utf-8") as f:
            lines = f.read().splitlines()

    for i, line in enumerate(lines):
        if line.strip().startswith("TELEGRAM_BOT_TOKEN="):
            lines[i] = f"TELEGRAM_BOT_TOKEN={token}"
            break
    else:
        lines.append(f"TELEGRAM_BOT_TOKEN={token}")

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _verify_token(token: str) -> tuple[bool | None, str]:
    """Tokenni Telegram serveridan tekshirish.

    Natija: (True, bot_username) — to'g'ri; (False, "") — noto'g'ri;
    (None, "") — tekshirib bo'lmadi (internet yo'q).
    """
    try:
        import httpx

        resp = httpx.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
    except Exception:
        return None, ""

    if resp.status_code == 200:
        try:
            username = resp.json()["result"]["username"]
        except Exception:
            username = ""
        return True, username
    if resp.status_code in (401, 404):
        return False, ""
    return None, ""


def _ask_token() -> str:
    """Foydalanuvchidan token so'rash. Bo'sh javob — bekor qilish."""
    print()
    print("🔑 Telegram bot tokenini kiriting.")
    print("   Token @BotFather dan olinadi: /mybots → bot → API Token")
    print("   (Bekor qilish uchun hech narsa yozmasdan Enter bosing)")
    print()

    while True:
        try:
            raw = input("Bot token: ")
        except (EOFError, KeyboardInterrupt):
            print()
            return ""

        token = _sanitize_token(raw)
        if not token:
            return ""

        if not TOKEN_PATTERN.match(token):
            print("❌ Token formati noto'g'ri. To'g'ri format: 123456789:AAF...  Qayta urinib ko'ring.")
            continue

        ok, username = _verify_token(token)
        if ok is False:
            print("❌ Telegram bu tokenni qabul qilmadi (Unauthorized).")
            print("   @BotFather da /mybots → bot → API Token orqali yangi tokenni oling.")
            continue
        if ok is True:
            print(f"✅ Token to'g'ri! Bot: @{username}")
        else:
            print("⚠️ Internet yo'q — token tekshirilmadi, lekin saqlanadi.")
        return token


def ensure_bot_token() -> bool:
    """Bot token sozlanganini ta'minlash. False — bot ishga tushirilmaydi."""
    token = _sanitize_token(_read_saved_token())

    if token and token != TOKEN_PLACEHOLDER:
        ok, username = _verify_token(token)
        if ok is not False:
            os.environ["TELEGRAM_BOT_TOKEN"] = token
            if username:
                print(f"🤖 Bot: @{username}")
            return True
        print("❌ Saqlangan TELEGRAM_BOT_TOKEN noto'g'ri (Telegram rad etdi).")

    token = _ask_token()
    if not token:
        return False

    _save_token(token)
    os.environ["TELEGRAM_BOT_TOKEN"] = token
    print("💾 Token .env fayliga saqlandi.")
    return True


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

    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)

    if args.seed:
        run_seed()
        return

    if args.api:
        print("🚀 API server ishga tushmoqda: http://localhost:8000")
        print("📊 Admin panel: http://localhost:8000/admin")
        run_api()
        return

    if args.bot:
        if not ensure_bot_token():
            print("❌ Token kiritilmadi — bot ishga tushirilmadi.")
            sys.exit(1)
        print("🤖 Telegram bot ishga tushmoqda...")
        run_bot()
        return

    # Ikkalasini ham ishga tushirish
    bot_ready = ensure_bot_token()
    if not bot_ready:
        print()
        print("⚠️ Token kiritilmadi — faqat API server ishga tushadi (bot ishlamaydi).")

    print("=" * 50)
    print("🏫 Maktab Turniket Tizimi")
    print("=" * 50)
    print("🚀 API:   http://localhost:8000")
    print("📊 Admin: http://localhost:8000/admin")
    print("📖 Docs:  http://localhost:8000/docs")
    print("=" * 50)

    api_proc = multiprocessing.Process(target=run_api, name="api-server")
    api_proc.start()

    bot_proc = None
    if bot_ready:
        bot_proc = multiprocessing.Process(target=run_bot, name="telegram-bot")
        bot_proc.start()

    try:
        api_proc.join()
        if bot_proc:
            bot_proc.join()
    except KeyboardInterrupt:
        print("\n⏹ To'xtatilmoqda...")
        api_proc.terminate()
        if bot_proc:
            bot_proc.terminate()


if __name__ == "__main__":
    main()
