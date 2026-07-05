@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Xabarnoma - Avtomatik yangilash
cd /d "%~dp0"

echo.
echo ====================================================
echo   XABARNOMA - Avtomatik yangilash
echo ====================================================
echo.

:: Python topish
set "PYCMD="
py -3.12 -c "print('ok')" >nul 2>&1 && set "PYCMD=py -3.12"
if not defined PYCMD py -3.11 -c "print('ok')" >nul 2>&1 && set "PYCMD=py -3.11"
if not defined PYCMD python -c "print('ok')" >nul 2>&1 && set "PYCMD=python"
if not defined PYCMD (
    echo [XATO] Python topilmadi!
    pause
    exit /b 1
)

set "TEMP_ZIP=%TEMP%\xabarnoma_update.zip"
set "TEMP_DIR=%TEMP%\xabarnoma_extract"
set "REPO=https://github.com/mexroj978-beep/my-first-project/archive/refs/heads/main.zip"

echo [1/5] GitHub dan yuklab olinmoqda...
del "%TEMP_ZIP%" >nul 2>&1
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"

curl -fsSL -o "%TEMP_ZIP%" "%REPO%"
if errorlevel 1 (
    echo [XATO] curl bilan yuklab bo'lmadi, PowerShell sinab ko'rilmoqda...
    powershell -ExecutionPolicy Bypass -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%REPO%' -OutFile '%TEMP_ZIP%' -UseBasicParsing } catch { exit 1 }"
    if errorlevel 1 (
        echo [XATO] Yuklab olish muvaffaqiyatsiz! Internetni tekshiring.
        pause
        exit /b 1
    )
)

if not exist "%TEMP_ZIP%" (
    echo [XATO] ZIP fayl yuklanmadi!
    pause
    exit /b 1
)
echo [OK] Yuklab olindi!

echo.
echo [2/5] Fayllar ochilmoqda...
mkdir "%TEMP_DIR%" >nul 2>&1
tar -xf "%TEMP_ZIP%" -C "%TEMP_DIR%" 2>nul
if errorlevel 1 (
    powershell -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%TEMP_ZIP%' -DestinationPath '%TEMP_DIR%' -Force"
)

set "SRC=%TEMP_DIR%\my-first-project-main"
if not exist "%SRC%\app" (
    echo [XATO] Fayllar ochilmadi!
    pause
    exit /b 1
)

echo [3/5] Yangi fayllar nusxalanmoqda...
if exist "app" rmdir /s /q app
xcopy /E /I /Y "%SRC%\app" "app\" >nul
if exist "scripts" rmdir /s /q scripts
xcopy /E /I /Y "%SRC%\scripts" "scripts\" >nul

for %%F in (requirements.txt start.py run_bot.py 1_API.bat 2_BOT.bat TOXTATISH.bat ishga_tushirish.bat .env.example) do (
    if exist "%SRC%\%%F" copy /Y "%SRC%\%%F" "%%F" >nul 2>&1
)
copy /Y "%SRC%\YANGILASH.bat" "YANGILASH.bat" >nul 2>&1
echo [OK] Fayllar yangilandi!

echo.
echo [4/5] Kutubxonalar o'rnatilmoqda...
if not exist "venv" %PYCMD% -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
pip install -r requirements.txt
if errorlevel 1 (
    echo [XATO] Kutubxonalar o'rnatilmadi!
    pause
    exit /b 1
)
echo [OK] Tayyor!

echo.
echo [5/5] Tozalash...
rmdir /s /q "%TEMP_DIR%" >nul 2>&1
del "%TEMP_ZIP%" >nul 2>&1

echo.
echo ====================================================
echo   MUVAFFAQIYATLI YANGILANDI!
echo ====================================================
echo.
echo Endi TOXTATISH.bat keyin ishga_tushirish.bat bosing
echo yoki bu oynada davom eting...
echo.
pause

start "Xabarnoma" cmd /k "cd /d %~dp0 && call venv\Scripts\activate.bat && python start.py"
timeout /t 4 >nul
start http://localhost:8000/admin
echo Brauzer ochildi. Ctrl+F5 bosing!
pause
