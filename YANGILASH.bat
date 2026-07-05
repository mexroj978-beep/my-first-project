@echo off
chcp 65001 >nul
title Loyihani yangilash
cd /d "%~dp0"

echo.
echo ========================================
echo   XABARNOMA - Yangi versiyani yuklab olish
echo ========================================
echo.
echo GitHub dan yangi fayllar yuklanmoqda...
echo.

where git >nul 2>&1
if %errorlevel%==0 (
    if exist ".git" (
        echo Git orqali yangilanmoqda...
        git pull
        goto :done
    )
)

echo Git topilmadi. Quyidagilarni qo'lda qiling:
echo.
echo 1. Brauzerda oching:
echo    https://github.com/mexroj978-beep/my-first-project
echo.
echo 2. Code -^> Download ZIP
echo.
echo 3. ZIP ni oching
echo.
echo 4. Ichidagi "app" papkasini nusxalab
echo    Desktop\xabarnoma\app ga YOPISHIB qo'ying
echo.
echo 5. requirements.txt ham almashtiring
echo.
echo 6. CMD da:
echo    cd Desktop\xabarnoma
echo    venv\Scripts\activate
echo    pip install -r requirements.txt
echo.
echo 7. ishga_tushirish.bat ni qayta bosing
echo.
pause
exit /b 0

:done
echo.
echo Kutubxonalar yangilanmoqda...
call venv\Scripts\activate.bat 2>nul
pip install -r requirements.txt -q

echo.
echo [OK] Yangilandi! ishga_tushirish.bat ni qayta ishga tushiring.
echo.
pause
