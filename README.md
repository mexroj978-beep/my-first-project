# Maktab Turniket + Telegram Bot

Turniket (tirniket) tizimi bilan integratsiya qilinadigan va ota-onalarga farzandlari maktabga **kirgani** yoki **chiqgani** haqida Telegram orqali xabar yuboradigan dastur.

## Imkoniyatlar

- Turniket webhook orqali kirish/chiqish voqealarini qabul qilish
- Ota-onalarga Telegram bot orqali avtomatik xabar yuborish
- Maktab, o'quvchi, ota-ona va turniket qurilmalarini boshqarish (Admin API)
- Ota-onalar bot orqali ro'yxatdan o'tishi (`/register <id>`)
- Davomat tarixi saqlanishi

## Texnologiyalar

- **Python 3.11+**
- **FastAPI** — REST API va webhook
- **SQLAlchemy** — ma'lumotlar bazasi
- **python-telegram-bot** — Telegram bot
- **SQLite** — standart DB (PostgreSQL ga o'tkazish mumkin)

## O'rnatish

```bash
# 1. Virtual muhit
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Kutubxonalarni o'rnatish
pip install -r requirements.txt

# 3. Sozlamalar
cp .env.example .env
# .env faylida TELEGRAM_BOT_TOKEN ni to'ldiring
```

### Telegram bot yaratish

1. Telegramda [@BotFather](https://t.me/BotFather) ga yozing
2. `/newbot` buyrug'ini yuboring
3. Olingan tokenni `.env` faylga qo'ying: `TELEGRAM_BOT_TOKEN=...`

## Ishga tushirish

**Terminal 1 — API server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Telegram bot:**
```bash
python run_bot.py
```

**Namuna ma'lumotlar (ixtiyoriy):**
```bash
python scripts/seed_data.py
```

API hujjatlari: http://localhost:8000/docs

## Ishlash tartibi

```
Turniket (karta skan) → POST /webhooks/turnstile → DB ga saqlash → Telegram xabar → Ota-ona
```

1. O'quvchi turniketdan o'tadi (karta/RFID)
2. Turniket tizimi webhook yuboradi
3. Dastur o'quvchini karta ID bo'yicha topadi
4. Bog'langan ota-onalarga Telegram xabar ketadi

## Turniket integratsiyasi

Turniket qurilmasi har safar skanerlashda quyidagi endpointga **POST** so'rov yuboradi:

```
POST /webhooks/turnstile
Header: X-Webhook-Secret: <WEBHOOK_SECRET>
Content-Type: application/json
```

**So'rov tanasi:**
```json
{
  "card_id": "CARD001",
  "device_code": "GATE_IN_01",
  "direction": "in",
  "event_time": "2026-07-04T08:15:00+05:00"
}
```

| Maydon | Tavsif |
|--------|--------|
| `card_id` | O'quvchi karta/RFID identifikatori |
| `device_code` | Turniket qurilma kodi |
| `direction` | `in` — kirish, `out` — chiqish |
| `event_time` | Voqea vaqti (ixtiyoriy) |

**Javob:**
```json
{
  "success": true,
  "message": "Ali Karimov - in qayd etildi",
  "event_id": 1,
  "student_name": "Ali Karimov",
  "notifications_sent": 1
}
```

### cURL misoli

```bash
curl -X POST http://localhost:8000/webhooks/turnstile \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: change-me-in-production" \
  -d '{
    "card_id": "CARD001",
    "device_code": "GATE_IN_01",
    "direction": "in"
  }'
```

## Ota-ona ro'yxatdan o'tishi

1. Admin ota-onani tizimga qo'shadi (API orqali)
2. Ota-onaga **Parent ID** beriladi (masalan: `1`)
3. Ota-ona Telegram botda yozadi: `/register 1`
4. Endi farzand turniketdan o'tganda xabar oladi

**Bot buyruqlari:**
| Buyruq | Vazifa |
|--------|--------|
| `/start` | Boshlash |
| `/register <id>` | Hisobni bog'lash |
| `/mystudents` | Farzandlar ro'yxati |
| `/help` | Yordam |

## Admin API

Barcha admin so'rovlarida header kerak: `X-Admin-Key: admin-secret-key`

| Method | Endpoint | Vazifa |
|--------|----------|--------|
| POST | `/api/schools` | Maktab qo'shish |
| POST | `/api/students` | O'quvchi qo'shish |
| POST | `/api/parents` | Ota-ona qo'shish |
| POST | `/api/parents/link` | Ota-ona ↔ o'quvchi bog'lash |
| POST | `/api/devices` | Turniket qo'shish |
| GET | `/api/attendance` | Davomat tarixi |

**O'quvchi qo'shish misoli:**
```bash
curl -X POST http://localhost:8000/api/students \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: admin-secret-key" \
  -d '{
    "school_id": 1,
    "first_name": "Ali",
    "last_name": "Karimov",
    "class_name": "5-A",
    "card_id": "CARD001"
  }'
```

## Telegram xabar namunasi

```
🏫✅ Farzandingiz haqida xabar

👤 Ali Karimov
📚 Sinf: 5-A
🏫 15-sonli maktab

⏰ Vaqt: 08:15 (04.07.2026)
📍 Joy: 1-qavat, asosiy eshik
📌 Farzandingiz maktabga kirdi.
```

## Loyiha strukturasi

```
app/
├── main.py              # FastAPI ilova
├── config.py            # Sozlamalar
├── database.py          # DB ulanish
├── models/              # Ma'lumotlar bazasi modellari
├── schemas/             # Pydantic sxemalar
├── services/            # Biznes logika
│   ├── attendance.py    # Davomat qayta ishlash
│   └── telegram.py      # Xabar yuborish
├── api/
│   ├── webhooks.py      # Turniket webhook
│   └── admin.py         # Admin API
└── bot/
    └── handlers.py      # Telegram bot
scripts/
└── seed_data.py         # Namuna ma'lumotlar
run_bot.py               # Bot ishga tushirish
requirements.txt
.env.example
```

## Production uchun tavsiyalar

- `WEBHOOK_SECRET` va `ADMIN_API_KEY` ni kuchli qiymatlarga almashtiring
- SQLite o'rniga **PostgreSQL** ishlating
- HTTPS orqali webhook qabul qiling
- Turniket tizimi IP whitelist qo'shing

## Litsenziya

MIT
