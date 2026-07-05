from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from app.api.admin import router as admin_router
from app.api.payments import pay_page_router, router as payment_router
from app.api.webhooks import router as webhook_router
from app.config import settings
from app.database import init_db

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Turniket integratsiyasi va ota-onalarga Telegram xabar yuborish tizimi",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router)
app.include_router(payment_router)
app.include_router(pay_page_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "status": "running",
        "admin": "/admin",
        "docs": "/docs",
        "webhook": "/webhooks/turnstile",
    }


@app.get("/admin")
async def admin_panel():
    content = (STATIC_DIR / "admin.html").read_text(encoding="utf-8")
    return Response(
        content=content,
        media_type="text/html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok", "telegram_configured": bool(settings.telegram_bot_token)}
