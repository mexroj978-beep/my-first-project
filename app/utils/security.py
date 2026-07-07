"""Xavfsizlik yordamchi funksiyalari."""
import secrets

from fastapi import HTTPException, Request

from app.config import settings


def generate_access_token() -> str:
    return secrets.token_urlsafe(32)


def get_client_ip(request: Request) -> str:
    if settings.trust_proxy_headers:
        cf_ip = request.headers.get("CF-Connecting-IP")
        if cf_ip:
            return cf_ip.strip()
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
    if request.client:
        return request.client.host
    return ""


def check_turnstile_ip(request: Request) -> None:
    allowed = settings.turnstile_allowed_ips
    if not allowed:
        return
    client_ip = get_client_ip(request)
    if client_ip not in allowed:
        raise HTTPException(403, f"Ruxsat etilmagan IP: {client_ip}")
