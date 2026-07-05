@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Maktab Xabarnoma v3
cd /d "%~dp0"

echo.
echo  ========================================
echo    MAKTAB XABARNOMA v3.0
echo  ========================================
echo.

:: Python 3.12/3.11 topish
set "PY="
for %%V in (3.12 3.11 3.13) do (
    py -%%V -c "print('ok')" >nul 2>&1 && set "PY=py -%%V" && goto :found
)
echo [XATO] Python 3.12 kerak! https://python.org/downloads/
pause & exit /b 1

:found
echo [OK] Python topildi

if exist venv\pyvenv.cfg (
    findstr "3.15" venv\pyvenv.cfg >nul 2>&1 && (
        echo Eski venv o'chirilmoqda...
        rmdir /s /q venv
    )
)

if not exist venv (
    echo Virtual muhit yaratilmoqda...
    %PY% -m venv venv
)

call venv\Scripts\activate.bat
python -m pip install -r requirements.txt -q

if not exist .env copy .env.example .env

echo.
echo  Dastur ishga tushmoqda...
echo  Admin: http://localhost:8000/admin
echo  BU OYNANI YOPMANG!
echo.
python start.py
pause
