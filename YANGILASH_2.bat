@echo off
chcp 65001 >nul
title Xabarnoma Yangilash
cd /d "%~dp0"
echo.
echo Yangilash boshlanmoqda...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0YANGILASH.ps1"
if errorlevel 1 (
    echo.
    echo PowerShell xato berdi. YANGILASH.bat ni sinab ko'ring.
    pause
)
