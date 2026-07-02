# Maktab Davomat Tizimi

Tirniket (turniket) tizimi bilan integratsiya qilinadigan va ota-onalarga **Telegram bot** orqali farzandlari maktabga kirgani/chiqqani haqida xabar yuboradigan dastur.

## Imkoniyatlar

- **Tirniket integratsiyasi** — HTTP webhook orqali kirish/chiqish voqealarini qabul qilish
- **Telegram bot** — ota-onalar farzandlarini ro'yxatdan o'tkazadi va bildirishnoma oladi
- **Oylik obuna** — xabarlar faqat obunasi faol ota-onalarga yuboriladi
- **Admin panel** — ota-onalar va to'lovlarni brauzer orqali boshqarish
- **O'zbek tilida** xabarlar va buyruqlar
- **Admin API** — o'quvchilarni tizimga qo'shish
- **CLI skript** — tez o'quvchi qo'shish

## Ishlash sxemasi

```
O'quvchi kartani tirniketga tekkizadi
        ↓
Tirniket tizimi → POST /api/turnstile/event
        ↓
Dastur o'quvchini topadi → obunasi faol ota-onalarga Telegram xabar yuboradi
```

## O'rnatish

### 1. Kutubxonalarni o'rnatish

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Telegram bot yaratish

1. Telegramda [@BotFather](https://t.me/BotFather) ga yozing
2. `/newbot` buyrug'ini yuboring va bot nomini kiriting
3. Olingan tokenni `.env` fayliga qo'ying

### 3. Sozlamalar

```bash
cp .env.example .env
```

`.env` faylini tahrirlang:

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TURNSTILE_API_KEY=turnstile_maxfiy_kalit
ADMIN_API_KEY=admin_maxfiy_kalit
SCHOOL_NAME=Maktab nomi
MONTHLY_SUBSCRIPTION_AMOUNT=30000
PAYMENT_INSTRUCTIONS=To'lov uchun maktab kassasi yoki karta raqamiga to'lang. Chekni admin tasdiqlaydi.
```

### 4. Ishga tushirish

```bash
python main.py
```

Server `http://localhost:8000` da ishlaydi.  
API hujjatlari: `http://localhost:8000/docs`  
Admin panel: `http://localhost:8000/admin`

## Foydalanish

### O'quvchi qo'shish (CLI)

```bash
python scripts/manage_students.py add "Ali Valiyev" "5-A" "CARD001"
```

Chiqish:
```
✅ Qo'shildi: Ali Valiyev (5-A)
   Karta ID: CARD001
   Ro'yxatdan o'tish kodi: XK7M2P9A
```

Bu kodni ota-onaga bering — ular botda `/royxat XK7M2P9A` deb yozadi.

### Ota-ona ro'yxatdan o'tishi (Telegram)

1. Botga `/start` yuborish
2. `/royxat ABC12345` — maktabdan olingan kod bilan bog'lash
3. `/tolov` — oylik obuna holati va to'lov yo'riqnomasini ko'rish
4. `/farzandlar` — bog'langan farzandlarni ko'rish

> Eslatma: ota-ona ro'yxatdan o'tgandan keyin ham xabar olish uchun obunasi faol bo'lishi kerak.

### Tirniket integratsiyasi

Tirniket tizimingiz har safar o'quvchi kirganda quyidagi so'rovni yuborishi kerak:

```http
POST /api/turnstile/event
Content-Type: application/json
X-Api-Key: turnstile_maxfiy_kalit

{
    "card_id": "CARD001",
    "event_type": "enter",
    "event_time": "2026-07-02T08:30:00",
    "device_id": "gate-main"
}
```

| Maydon | Tavsif |
|--------|--------|
| `card_id` | RFID karta yoki tirniketdagi identifikator |
| `event_type` | `"enter"` (kirish) yoki `"exit"` (chiqish) |
| `event_time` | Voqea vaqti (ixtiyoriy, ISO format) |
| `device_id` | Tirniket qurilma ID (ixtiyoriy) |

**Ota-onaga keladigan xabar misoli:**

> 📢 **Maktab nomi**
>
> 👤 **Ali Valiyev** (5-A-sinf)  
> ✅ Farzandingiz maktabga kirdi.
>
> 🕐 Vaqt: 08:30  
> 📅 Sana: 02.07.2026

### Admin API

Brauzerda `http://localhost:8000/admin` sahifasini oching, `ADMIN_API_KEY` ni kiriting va:

- ota-onalar ro'yxatini ko'ring
- qaysi ota-onaning obunasi faol yoki muddati tugaganini tekshiring
- to'lov kiritib obunani 1 yoki bir nechta oyga uzaytiring

To'lov kiritilganda obuna muddati:

- agar obuna hali faol bo'lsa — mavjud muddat ustiga qo'shiladi
- agar muddati tugagan bo'lsa — bugundan boshlab hisoblanadi

#### API orqali boshqarish

O'quvchi qo'shish:

```bash
curl -X POST http://localhost:8000/api/admin/students \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: admin_maxfiy_kalit" \
  -d '{"full_name": "Ali Valiyev", "class_name": "5-A", "card_id": "CARD001"}'
```

Ota-onalar va obuna holatini ko'rish:

```bash
curl http://localhost:8000/api/admin/parents \
  -H "X-Admin-Key: admin_maxfiy_kalit"
```

To'lov kiritish va obunani faollashtirish:

```bash
curl -X POST http://localhost:8000/api/admin/payments \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: admin_maxfiy_kalit" \
  -d '{"telegram_id": 123456789, "months": 1, "amount_som": 30000, "note": "Iyul oyi"}'
```

## Tirniket tizimlari bilan bog'lash

Ko'pchilik zamonaviy tirniket tizimlari (Hikvision, ZKTeco, Dahua va boshqalar) HTTP webhook yoki middleware orqali voqealarni tashqi serverga yuborishni qo'llab-quvvatlaydi. Quyidagi usullardan birini tanlang:

1. **To'g'ridan-to'g'ri webhook** — tirniket sozlamalarida URL va API kalitni ko'rsating
2. **Middleware / adapter** — tirniket SDK yoki log fayllarini o'qib, ushbu API ga yuboradigan kichik skript yozing
3. **Test uchun** — `curl` yoki Postman bilan `/api/turnstile/event` ga so'rov yuboring

## Loyiha tuzilmasi

```
├── main.py                  # Asosiy server
├── app/
│   ├── api/routes.py        # REST API (tirniket + admin)
│   ├── bot/telegram_bot.py # Telegram bot
│   ├── models.py            # Ma'lumotlar bazasi modellari
│   └── services/
│       ├── attendance.py
│       └── subscriptions.py
├── scripts/manage_students.py
├── requirements.txt
└── .env.example
```

## Texnologiyalar

- **Python 3.11+**
- **FastAPI** — REST API
- **aiogram 3** — Telegram bot
- **SQLAlchemy** — ma'lumotlar bazasi (SQLite standart)

## Keyingi qadamlar (ixtiyoriy)

- Click/Payme avtomatik to'lov webhooklari
- Maktabdan chiqish vaqtini ham hisobot qilish
- Bir nechta maktab filiali qo'llab-quvvatlash
- PostgreSQL ga o'tish (katta maktablar uchun)
