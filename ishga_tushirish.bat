@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Maktab Xabarnoma Tizimi
cd /d "%~dp0"

echo.
echo ========================================
echo   Maktab Turniket + Telegram Bot
echo   Papka: xabarnoma
echo ========================================
echo.
echo DIQQAT: Agar 1_API.bat yoki 2_BOT.bat ochiq bo'lsa,
echo avval TOXTATISH.bat ni bosing!
echo.

:: Faqat Python 3.12 yoki 3.11 qidirish (3.15 ISHLATMAYDI!)
set "PYCMD="

py -3.12 -c "import sys; print(sys.version)" >nul 2>&1
if %errorlevel%==0 set "PYCMD=py -3.12"

if not defined PYCMD (
    py -3.11 -c "import sys; print(sys.version)" >nul 2>&1
    if !errorlevel!==0 set "PYCMD=py -3.11"
)

if not defined PYCMD (
    py -3.13 -c "import sys; print(sys.version)" >nul 2>&1
    if !errorlevel!==0 set "PYCMD=py -3.13"
)

if not defined PYCMD (
    echo.
    echo [XATO] Python 3.12 topilmadi!
    echo.
    echo Sizda Python 3.15 bor - u MOS EMAS.
    echo.
    echo ========================================
    echo   QILISH KERAK:
    echo ========================================
    echo.
    echo 1. Python 3.12 yuklab oling:
    echo    https://www.python.org/downloads/release/python-3120/
    echo    "Windows installer 64-bit" ni bosing
    echo.
    echo 2. O'rnatishda belgilang:
    echo    [x] Add python.exe to PATH
    echo.
    echo 3. "venv" papkasini o'chiring
    echo.
    echo 4. Bu faylni qayta bosing
    echo.
    echo ========================================
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('%PYCMD% --version 2^>^&1') do set PYVER=%%v
echo [OK] %PYVER% topildi
echo.

:: venv har doim to'g'ri Python bilan qayta yaratilsin
if exist "venv" (
    echo Eski venv o'chirilmoqda...
    rmdir /s /q venv
)

echo Virtual muhit yaratilmoqda (%PYCMD%)...
%PYCMD% -m venv venv
if errorlevel 1 (
    echo [XATO] venv yaratib bo'lmadi!
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

:: Tekshirish: venv ichida 3.15 bo'lmasin
findstr /C:"3.15" "venv\pyvenv.cfg" >nul 2>&1
if %errorlevel%==0 (
    echo.
    echo [XATO] venv yana Python 3.15 bilan yaratildi!
    echo Python 3.12 ni qayta o'rnating va PATH ni tekshiring.
    pause
    exit /b 1
)

echo pip yangilanmoqda...
python -m pip install --upgrade pip -q

echo Kutubxonalar o'rnatilmoqda (1-2 daqiqa)...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [XATO] O'rnatish muvaffaqiyatsiz!
    echo Python 3.12 o'rnatilganini tekshiring: py -3.12 --version
    pause
    exit /b 1
)

if not exist ".env" (
    copy .env.example .env
    echo.
    echo DIQQAT: .env faylini oching va TELEGRAM_BOT_TOKEN ni kiriting!
    echo.
    pause
)

echo.
echo ========================================
echo   TAYYOR! Dastur ishga tushmoqda
echo   Admin: http://localhost:8000/admin
echo ========================================
echo.
python start.py
pause
