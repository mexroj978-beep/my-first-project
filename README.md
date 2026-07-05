# Maktab Xabarnoma v3.0

Turniket integratsiyasi + ota-onalarga Telegram xabar + obuna tizimi.

## Tez boshlash (Windows)

```
1. Python 3.12 o'rnating (Add to PATH belgilang)
2. .env.example ni .env ga nusxalang
3. TELEGRAM_BOT_TOKEN qo'ying
4. ishga_tushirish.bat ni bosing
5. http://localhost:8000/admin
```

## Imkoniyatlar

- Turniket webhook — kirish/chiqish qayd etish
- Telegram bot — ota-onalarga xabar
- 3 kun bepul sinov, keyin obuna
- `/pay` — to'lov, obuna avtomatik yoqiladi
- Admin panel — CRUD, obuna sozlash
- Click to'lov integratsiyasi

## Bot buyruqlari

| Buyruq | Vazifa |
|--------|--------|
| /register 1 | Ro'yxatdan o'tish |
| /pay | To'lov (avtomatik obuna) |
| /status | Obuna holati |
| /mystudents | Farzandlar |

## Turniket webhook

```
POST /webhooks/turnstile
Header: X-Webhook-Secret: ...
Body: {"card_id":"001","device_code":"GATE_IN_01","direction":"in"}
```

## Fayllar

| Fayl | Vazifa |
|------|--------|
| ishga_tushirish.bat | Dasturni ishga tushirish |
| TOXTATISH.bat | To'xtatish |
| scripts/seed.py | Namuna ma'lumotlar |
