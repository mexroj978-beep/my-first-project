@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe scripts\backup_db.py -o backups
) else (
    python scripts\backup_db.py -o backups
)
pause
