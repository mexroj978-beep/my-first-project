#!/usr/bin/env python3
"""API + Bot ishga tushirish."""
import argparse, multiprocessing, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def api():
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)

def bot():
    from app.bot.handlers import run_bot
    run_bot()

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--api", action="store_true")
    p.add_argument("--bot", action="store_true")
    a = p.parse_args()
    if a.api:
        print("🚀 http://localhost:8000/admin")
        api()
    elif a.bot:
        bot()
    else:
        print("=" * 40)
        print("  Maktab Xabarnoma v3.0")
        print("  Admin: http://localhost:8000/admin")
        print("=" * 40)
        pa = multiprocessing.Process(target=api)
        pb = multiprocessing.Process(target=bot)
        pa.start(); pb.start()
        pa.join(); pb.join()
