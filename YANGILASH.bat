@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Xabarnoma - Avtomatik yangilash
cd /d "%~dp0"

echo.
echo ====================================================
echo   XABARNOMA - Avtomatik yangilash
echo   Barcha yangi funksiyalar o'rnatiladi
echo ====================================================
echo.

:: Python tekshirish
set "PYCMD="
py -3.12 -c "print('ok')" >nul 2>&1 && set "PYCMD=py -3.12"
if not defined PYCMD py -3.11 -c "print('ok')" >nul 2>&1 && set "PYCMD=py -3.11"
if not defined PYCMD python -c "print('ok')" >nul 2>&1 && set "PYCMD=python"

if not defined PYCMD (
    echo [XATO] Python topilmadi! Avval Python 3.12 o'rnating.
    pause
    exit /b 1
)

echo [1/5] GitHub dan yangi fayllar yuklanmoqda...
set "TEMP_ZIP=%TEMP%\xabarnoma_update.zip"
set "TEMP_DIR=%TEMP%\xabarnoma_update"
set "REPO=https://github.com/mexroj978-beep/my-first-project/archive/refs/heads/main.zip"

powershell -NoProfile -Command ^
  "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ^
   Invoke-WebRequest -Uri '%REPO%' -OutFile '%TEMP_ZIP%' -UseBasicParsing; ^
   if (Test-Path '%TEMP_DIR%') { Remove-Item '%TEMP_DIR%' -Recurse -Force }; ^
   Expand-Archive -Path '%TEMP_ZIP%' -DestinationPath '%TEMP_DIR%' -Force"

if not exist "%TEMP_DIR%\my-first-project-main\app" (
    echo [XATO] Yuklab olish muvaffaqiyatsiz! Internetni tekshiring.
    pause
    exit /b 1
)
echo [OK] Yuklab olindi!

echo.
echo [2/5] Eski fayllar yangilanmoqda...

:: app papkasini almashtirish
if exist "app" rmdir /s /q app
xcopy /E /I /Y "%TEMP_DIR%\my-first-project-main\app" "app\" >nul

:: scripts papkasini almashtirish
if exist "scripts" rmdir /s /q scripts
xcopy /E /I /Y "%TEMP_DIR%\my-first-project-main\scripts" "scripts\" >nul

:: Asosiy fayllarni nusxalash
for %%F in (
    requirements.txt
    start.py
    run_bot.py
    1_API.bat
    2_BOT.bat
    TOXTATISH.bat
    ishga_tushirish.bat
    .env.example
) do (
    if exist "%TEMP_DIR%\my-first-project-main\%%F" (
        copy /Y "%TEMP_DIR%\my-first-project-main\%%F" "%%F" >nul 2>&1
    )
)

echo [OK] Fayllar yangilandi!

echo.
echo [3/5] Virtual muhit tekshirilmoqda...
if not exist "venv" (
    echo Virtual muhit yaratilmoqda...
    %PYCMD% -m venv venv
)

echo.
echo [4/5] Kutubxonalar o'rnatilmoqda...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
pip install -r requirements.txt
if errorlevel 1 (
    echo [XATO] Kutubxonalar o'rnatilmadi!
    pause
    exit /b 1
)
echo [OK] Kutubxonalar tayyor!

echo.
echo [5/5] Tozalash...
rmdir /s /q "%TEMP_DIR%" 2>nul
del "%TEMP_ZIP%" 2>nul

echo.
echo ====================================================
echo   MUVAFFAQIYATLI YANGILANDI!
echo ====================================================
echo.
echo Yangi funksiyalar:
echo   - Obuna bo'limi (narx sozlash)
echo   - O'quvchi/Ota-ona tahrirlash va o'chirish
echo   - Obuna+ tugmasi
echo   - /pay - avtomatik to'lov va obuna
echo.
echo Endi ishga_tushirish.bat ni bosing!
echo.
pause

:: Avtomatik ishga tushirish
echo Dastur ishga tushmoqda...
start "Xabarnoma API+Bot" cmd /k "cd /d %~dp0 && call venv\Scripts\activate.bat && python start.py"

timeout /t 3 >nul
start http://localhost:8000/admin

echo.
echo Brauzer ochildi: http://localhost:8000/admin
echo Ctrl+F5 bosing (kesh tozalash)
pause
