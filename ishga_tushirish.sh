#!/bin/bash
cd "$(dirname "$0")"

echo "========================================"
echo "  Maktab Turniket + Telegram Bot"
echo "  Papka: xabarnoma"
echo "========================================"

if [ ! -d "venv" ]; then
    echo "Virtual muhit yaratilmoqda..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt -q

if [ ! -f ".env" ]; then
    cp .env.example .env
fi

echo ""
echo "Dastur ishga tushmoqda..."
echo "Admin panel: http://localhost:8000/admin"
echo "(Birinchi ishga tushirishda dastur bot tokenini so'raydi)"
echo ""
python start.py
