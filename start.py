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
import sys


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
        print("🤖 Telegram bot ishga tushmoqda...")
        run_bot()
        return

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
