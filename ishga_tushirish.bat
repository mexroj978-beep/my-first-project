@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Maktab Xabarnoma Tizimi
cd /d "%~dp0"

echo ========================================
echo   Maktab Turniket + Telegram Bot
echo   Papka: xabarnoma
echo ========================================
echo.

:: Python 3.12 yoki 3.11 ni topish (3.15 mos emas!)
set "PYCMD="
where py >nul 2>&1
if %errorlevel%==0 (
    py -3.12 -c "print('ok')" >nul 2>&1
    if !errorlevel!==0 set "PYCMD=py -3.12"
)
if not defined PYCMD (
    py -3.11 -c "print('ok')" >nul 2>&1
    if !errorlevel!==0 set "PYCMD=py -3.11"
)
if not defined PYCMD (
    py -3.13 -c "print('ok')" >nul 2>&1
    if !errorlevel!==0 set "PYCMD=py -3.13"
)
if not defined PYCMD (
    python -c "print('ok')" >nul 2>&1
    if !errorlevel!==0 set "PYCMD=python"
)

if not defined PYCMD (
    echo [XATO] Python topilmadi!
    echo.
    echo Python 3.12 ni o'rnating:
    echo https://www.python.org/downloads/release/python-3120/
    echo.
    echo O'rnatishda "Add Python to PATH" ni belgilang!
    pause
    exit /b 1
)

:: Python versiyasini tekshirish
for /f "tokens=2 delims= " %%v in ('%PYCMD% --version 2^>^&1') do set PYVER=%%v
echo Python versiyasi: %PYVER%
echo.

echo %PYVER% | findstr /R "^3\.1[5-9]\." >nul
if %errorlevel%==0 (
    echo [XATO] Python %PYVER% juda yangi - dastur bilan mos emas!
    echo.
    echo YECHIM:
    echo   1. Python 3.12 ni o'rnating:
    echo      https://www.python.org/downloads/release/python-3120/
    echo   2. "venv" papkasini o'chiring
    echo   3. ishga_tushirish.bat ni qayta bosing
    echo.
    pause
    exit /b 1
)

:: Eski venv noto'g'ri Python bilan yaratilgan bo'lsa - o'chirish
if exist "venv\pyvenv.cfg" (
    findstr /C:"3.15" "venv\pyvenv.cfg" >nul 2>&1
    if %errorlevel%==0 (
        echo Eski venv Python 3.15 bilan yaratilgan - yangilanmoqda...
        rmdir /s /q venv
    )
)

if not exist "venv" (
    echo Virtual muhit yaratilmoqda (%PYCMD%)...
    %PYCMD% -m venv venv
    if errorlevel 1 (
        echo [XATO] venv yaratib bo'lmadi!
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat

echo pip yangilanmoqda...
python -m pip install --upgrade pip setuptools wheel -q

echo Kutubxonalar o'rnatilmoqda...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [XATO] Kutubxonalar o'rnatilmadi!
    echo.
    echo YECHIM:
    echo   1. "venv" papkasini o'chiring
    echo   2. Python 3.12 o'rnating
    echo   3. Qayta urinib ko'ring
    echo.
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
echo   Dastur ishga tushmoqda!
echo   Admin panel: http://localhost:8000/admin
echo ========================================
echo.
python start.py

pause
