@echo off
chcp 65001 >nul
title Python versiyasini tekshirish
echo.
echo ========================================
echo   PYTHON TEKSHIRUV
echo ========================================
echo.

echo Python 3.15 (MOS EMAS):
python --version 2>nul
echo.

echo Python 3.12 (KERAK):
py -3.12 --version 2>nul
if errorlevel 1 echo   [XATO] Python 3.12 topilmadi!
echo.

echo Python 3.11:
py -3.11 --version 2>nul
echo.

echo ========================================
echo.
echo Agar "Python 3.12 topilmadi" desa:
echo   1. https://www.python.org/downloads/release/python-3120/
echo   2. Windows installer 64-bit ni o'rnating
echo   3. [x] Add python.exe to PATH belgilang
echo   4. Kompyuterni qayta yoqing
echo.
pause
