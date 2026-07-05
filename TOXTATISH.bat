@echo off
chcp 65001 >nul
title To'xtatish
echo Dastur to'xtatilmoqda...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
echo [OK] To'xtatildi. Endi ishga_tushirish.bat ni bosing.
pause
