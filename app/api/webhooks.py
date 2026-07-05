from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas import TurnstileEvent, TurnstileResponse
from app.services.attendance import AttendanceService

router = APIRouter(prefix="/webhooks", tags=["Turniket"])


@router.post("/turnstile", response_model=TurnstileResponse)
async def turnstile(ev: TurnstileEvent, x: str = Header(..., alias="X-Webhook-Secret"), db: AsyncSession = Depends(get_db)):
    if x != settings.webhook_secret:
        raise HTTPException(401, "Noto'g'ri kalit")
    svc = AttendanceService()
    att, msg, sent, name = await svc.process(db, ev)
    if not att:
        return TurnstileResponse(success=False, message=msg)
    return TurnstileResponse(success=True, message=msg, event_id=att.id, student_name=name, notifications_sent=sent)
