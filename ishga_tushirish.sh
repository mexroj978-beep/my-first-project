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

echo ""
echo "Dastur ishga tushmoqda..."
echo "Admin panel: http://localhost:8000/admin"
echo ""
python start.py
