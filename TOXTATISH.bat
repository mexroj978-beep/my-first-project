@echo off
chcp 65001 >nul
title Dasturni to'xtatish
echo.
echo ========================================
echo   Barcha dastur jarayonlari to'xtatilmoqda
echo ========================================
echo.

:: 8000-portdagi jarayonni to'xtatish
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Port 8000: jarayon %%a to'xtatilmoqda...
    taskkill /F /PID %%a >nul 2>&1
)

:: Python jarayonlari (xabarnoma papkasidagi)
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1

echo.
echo [OK] Hammasi to'xtatildi!
echo.
echo Endi faqat BITTASINI ishga tushiring:
echo   1_API.bat  (1-oyna)
echo   2_BOT.bat  (2-oyna)
echo.
echo YOKI faqat ishga_tushirish.bat (ikkalasi birga)
echo.
pause
