@echo off
chcp 65001 >nul
title API Server
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo.
echo API server ishga tushmoqda...
echo Admin panel: http://localhost:8000/admin
echo.
echo BU OYNANI YOPMANG!
echo.
python start.py --api
pause
