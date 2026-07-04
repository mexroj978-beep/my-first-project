@echo off
chcp 65001 >nul
title Xabarnoma - Ish stoliga o'rnatish

set "TARGET=%USERPROFILE%\Desktop\xabarnoma"
set "SOURCE=%~dp0"

echo.
echo ==========================================
echo   XABARNOMA - Ish stoliga o'rnatish
echo ==========================================
echo.
echo Papka manzili:
echo %TARGET%
echo.

:: Papka yaratish
if not exist "%TARGET%" (
    mkdir "%TARGET%"
    echo [OK] xabarnoma papkasi yaratildi
) else (
    echo [OK] xabarnoma papkasi allaqachon bor
)

echo.
echo Fayllar nusxalanmoqda, biroz kuting...

:: app va scripts papkalarini ko'chirish
if exist "%SOURCE%app" (
    robocopy "%SOURCE%app" "%TARGET%\app" /E /NFL /NDL /NJH /NJS /nc /ns /np >nul
)
if exist "%SOURCE%scripts" (
    robocopy "%SOURCE%scripts" "%TARGET%\scripts" /E /NFL /NDL /NJH /NJS /nc /ns /np >nul
)

:: Asosiy fayllarni ko'chirish
for %%F in (
    requirements.txt
    start.py
    run_bot.py
    README.md
    QOLLANMA.txt
    .env.example
    .gitignore
    ishga_tushirish.bat
    ishga_tushirish.sh
) do (
    if exist "%SOURCE%%%F" copy /Y "%SOURCE%%%F" "%TARGET%\" >nul 2>&1
)

echo.
echo ==========================================
echo   MUVAFFAQIYATLI O'RNATILDI!
echo ==========================================
echo.
echo Endi quyidagilarni qiling:
echo.
echo   1. Ish stolidagi "xabarnoma" papkasini oching
echo   2. "ishga_tushirish.bat" ni ikki marta bosing
echo.
echo Papka hozir ochiladi...
echo.

timeout /t 3 >nul
explorer "%TARGET%"
pause
