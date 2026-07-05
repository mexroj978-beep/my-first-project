@echo off
chcp 65001 >nul
title Telegram Bot
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo.
echo Telegram bot ishga tushmoqda...
echo Bot: @Dilbandimbot
echo.
echo BU OYNANI YOPMANG!
echo Keyin Telegramda yozing: /register 1
echo.
python start.py --bot
pause
