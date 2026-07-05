@echo off
chcp 65001 >nul
title Versiya tekshirish
cd /d "%~dp0"
echo.
echo ========================================
echo   VERSIYA TEKSHIRUV
echo ========================================
echo.
findstr /C:"Obuna" "app\static\admin.html" >nul 2>&1
if errorlevel 1 (
    echo [XATO] ESKI versiya! YANGILASH_2.bat ni bosing.
) else (
    echo [OK] YANGI versiya v2.1 topildi!
    findstr /C:"v2.1" "app\static\admin.html" >nul 2>&1 && echo [OK] Obuna, tahrirlash, to'lov mavjud.
)
echo.
findstr /C:"subscription" "app\static\admin.html" >nul 2>&1 && echo - Obuna tab: BOR || echo - Obuna tab: YOQ
findstr /C:"btn-edit" "app\static\admin.html" >nul 2>&1 && echo - Tahrirlash tugmasi: BOR || echo - Tahrirlash tugmasi: YOQ
findstr /C:"activateSub" "app\static\admin.html" >nul 2>&1 && echo - Obuna+ tugmasi: BOR || echo - Obuna+ tugmasi: YOQ
echo.
pause
