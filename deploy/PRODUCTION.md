# Production sozlash — Maktab Xabarnoma

## 1. `.env` (production)

```env
TELEGRAM_BOT_TOKEN=...
ADMIN_API_KEY=<murakkab-tasodifiy-kalit>
WEBHOOK_SECRET=<murakkab-tasodifiy-kalit>

# PostgreSQL (tavsiya etiladi)
DATABASE_URL=postgresql+asyncpg://xabarnoma:PAROL@localhost:5432/xabarnoma

# HTTPS manzil
APP_BASE_URL=https://xabarnoma.example.com
TRUST_PROXY_HEADERS=true

PAYMENT_DEMO_MODE=false

# Turniket / Face ID qurilma IP lari (vergul bilan)
TURNSTILE_IP_WHITELIST=192.168.1.100,192.168.1.101
```

## 2. PostgreSQL o'rnatish (Ubuntu)

```bash
sudo apt install postgresql postgresql-contrib
sudo -u postgres createuser -P xabarnoma
sudo -u postgres createdb -O xabarnoma xabarnoma
pip install asyncpg
```

`.env` da `DATABASE_URL=postgresql+asyncpg://...` qo'ying va dasturni ishga tushiring — jadvallar avtomatik yaratiladi.

## 3. HTTPS — nginx + Let's Encrypt

```bash
sudo apt install nginx certbot python3-certbot-nginx
sudo cp deploy/nginx-xabarnoma.conf /etc/nginx/sites-available/xabarnoma
# Domen nomini tahrirlang: xabarnoma.example.com
sudo ln -s /etc/nginx/sites-available/xabarnoma /etc/nginx/sites-enabled/
sudo certbot --nginx -d xabarnoma.example.com
sudo nginx -t && sudo systemctl reload nginx
```

`.env`:
```
APP_BASE_URL=https://xabarnoma.example.com
TRUST_PROXY_HEADERS=true
```

## 4. HTTPS — Cloudflare (alternativa)

1. Domenni Cloudflare ga ulang
2. SSL/TLS → **Full (strict)**
3. DNS → A yozuvi server IP ga
4. Turniket webhook uchun **TURNSTILE_IP_WHITELIST** da haqiqiy qurilma IP sini yozing
5. `TRUST_PROXY_HEADERS=true` (Cloudflare `CF-Connecting-IP` uchun nginx da sozlash kerak bo'lishi mumkin)

## 5. Turniket IP whitelist

`.env`:
```
TURNSTILE_IP_WHITELIST=203.0.113.50,10.0.0.5
```

- **Bo'sh qoldirilsa** — barcha IP lar ruxsat (mahalliy test uchun)
- **To'ldirilsa** — faqat shu IP lardan `POST /webhooks/turnstile` qabul qilinadi

## 6. Zaxira nusxa (backup)

```bash
# SQLite
python scripts/backup_db.py

# PostgreSQL (pg_dump kerak)
python scripts/backup_db.py -o /var/backups/xabarnoma
```

Kunlik zaxira (cron):
```
0 2 * * * cd /opt/xabarnoma && /opt/xabarnoma/venv/bin/python scripts/backup_db.py -o /var/backups/xabarnoma
```

## 7. Ro'yxatdan o'tish (telefon tekshiruvi)

Ota-ona botda:
```
/register 5 901234567
```
Admin panelda kiritilgan telefon raqam bilan mos kelishi kerak.

## 8. To'lov havolasi

Buyurtmalar endi tasodifiy token bilan:
```
https://xabarnoma.example.com/pay/AbCdEf123...
```
Eski raqamli havolalar (`/pay/1`) ham ishlaydi (mos kelish).

## 9. Systemd xizmati (ixtiyoriy)

`/etc/systemd/system/xabarnoma.service`:
```ini
[Unit]
Description=Maktab Xabarnoma
After=network.target postgresql.service

[Service]
User=xabarnoma
WorkingDirectory=/opt/xabarnoma
EnvironmentFile=/opt/xabarnoma/.env
ExecStart=/opt/xabarnoma/venv/bin/python start.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now xabarnoma
```
