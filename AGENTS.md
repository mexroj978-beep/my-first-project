# AGENTS.md

## Cursor Cloud specific instructions

Product: **Maktab Xabarnoma / Turniket Tizimi v3.0** — a FastAPI + Telegram bot app for school
turnstile attendance tracking with parent notifications and subscriptions. Single Python product
(not a monorepo). UI/docs are in Uzbek. See `README.md` and `deploy/PRODUCTION.md`.

### Environment
- Python 3.12, dependencies installed into a virtualenv at `./venv` (created by the startup update script).
- Always invoke tools via the venv, e.g. `./venv/bin/python`, `./venv/bin/pytest`.
- No linter or build step is configured (pure Python + a single static `app/static/admin.html`).

### Running the app (dev)
- API only: `./venv/bin/python start.py --api` → serves on `http://0.0.0.0:8000`, admin panel at `/admin`.
- API + Telegram bot: `./venv/bin/python start.py` (bot process needs a valid `TELEGRAM_BOT_TOKEN`).
- Bot only: `./venv/bin/python start.py --bot`.
- Health check: `GET /health` → `{"ok":true,"telegram":<bool>}`. `telegram` is `false` when no bot
  token is set; this is expected and does not indicate a failure of the API.

### Non-obvious gotchas
- `.env` is **optional**: `app/config.py` has working defaults matching `.env.example` (SQLite DB,
  demo payment mode, admin key `admin-secret-key`, webhook secret `change-me-in-production`). Only
  create `.env` (from `.env.example`) if you need to set `TELEGRAM_BOT_TOKEN` or override defaults.
  `.env` is gitignored.
- Standalone scripts import the `app` package, so run them from the repo root with `PYTHONPATH`:
  `PYTHONPATH=/workspace ./venv/bin/python scripts/seed.py` (same for `scripts/backup_db.py`).
  `start.py`/uvicorn set up the path themselves and do not need this.
- The DB is SQLite (`xabarnoma.db`, auto-created/migrated on startup). Seed sample data with
  `PYTHONPATH=/workspace ./venv/bin/python scripts/seed.py`.
- `pytest` is not in `requirements.txt`; the update script installs it separately.

### Admin API / webhook quick reference
- Admin REST API is under `/api/*` and requires header `X-Admin-Key: admin-secret-key` (default).
- Turnstile webhook: `POST /webhooks/turnstile` with header `X-Webhook-Secret: change-me-in-production`
  and body `{"card_id":"001","device_code":"GATE_IN_01","direction":"in"}`.

### Tests
- `./venv/bin/python -m pytest tests/` (currently only phone-normalization tests).
