@echo off
chcp 65001 >nul
title Maktab Xabarnoma Tizimi
cd /d "%~dp0"

echo ========================================
echo   Maktab Turniket + Telegram Bot
echo   Papka: xabarnoma
echo ========================================
echo.

if not exist "venv" (
    echo Virtual muhit yaratilmoqda...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Kutubxonalar o'rnatilmoqda...
pip install -r requirements.txt -q

if not exist ".env" (
    copy .env.example .env
    echo.
    echo DIQQAT: .env faylini oching va TELEGRAM_BOT_TOKEN ni kiriting!
    echo.
    pause
)

echo.
echo Dastur ishga tushmoqda...
echo Admin panel: http://localhost:8000/admin
echo.
python start.py

pause
