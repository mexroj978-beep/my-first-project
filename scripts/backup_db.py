#!/usr/bin/env python3
"""Ma'lumotlar bazasi zaxira nusxasi (SQLite yoki PostgreSQL)."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

# Loyiha ildizidan .env o'qish
ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

from app.config import settings  # noqa: E402


def backup_sqlite(url: str, out_dir: Path) -> Path:
    # sqlite+aiosqlite:///./xabarnoma.db
    path = url.split("///", 1)[-1]
    db_path = Path(path)
    if not db_path.is_absolute():
        db_path = ROOT / db_path
    if not db_path.exists():
        raise FileNotFoundError(f"Baza topilmadi: {db_path}")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = out_dir / f"xabarnoma_{stamp}.db"
    shutil.copy2(db_path, dest)
    return dest


def backup_postgres(url: str, out_dir: Path) -> Path:
    # postgresql+asyncpg://user:pass@host:5432/dbname
    parsed = urlparse(url.replace("+asyncpg", ""))
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = out_dir / f"xabarnoma_{stamp}.sql"
    env = os.environ.copy()
    if parsed.password:
        env["PGPASSWORD"] = parsed.password
    cmd = [
        "pg_dump",
        "-h", parsed.hostname or "localhost",
        "-p", str(parsed.port or 5432),
        "-U", parsed.username or "postgres",
        "-d", (parsed.path or "/xabarnoma").lstrip("/"),
        "-f", str(dest),
        "--no-owner",
    ]
    subprocess.run(cmd, check=True, env=env)
    return dest


def main():
    p = argparse.ArgumentParser(description="Xabarnoma DB zaxira nusxasi")
    p.add_argument("-o", "--output", default="backups", help="Zaxira papkasi")
    args = p.parse_args()
    out_dir = Path(args.output)
    url = settings.database_url

    if "sqlite" in url:
        dest = backup_sqlite(url, out_dir)
    elif "postgresql" in url:
        dest = backup_postgres(url, out_dir)
    else:
        raise SystemExit(f"Qo'llab-quvvatlanmaydigan DATABASE_URL: {url}")

    print(f"✅ Zaxira yaratildi: {dest}")


if __name__ == "__main__":
    main()
