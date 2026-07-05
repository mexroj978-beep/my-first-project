from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.api.admin import router as admin_router
from app.api.payments import router as pay_router, wh as pay_wh
from app.api.webhooks import router as wh_router
from app.config import settings
from app.database import init_db

STATIC = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title=settings.app_name, version="3.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(wh_router)
app.include_router(pay_wh)
app.include_router(pay_router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {"app": settings.app_name, "version": "3.0", "admin": "/admin"}


@app.get("/admin")
def admin():
    html = (STATIC / "admin.html").read_text(encoding="utf-8")
    return Response(html, media_type="text/html", headers={"Cache-Control": "no-store"})


@app.get("/health")
def health():
    return {"ok": True, "telegram": bool(settings.telegram_bot_token)}
