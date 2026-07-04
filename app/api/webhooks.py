from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas import TurnstileEvent, TurnstileEventResponse
from app.services.attendance import AttendanceService

router = APIRouter(prefix="/webhooks", tags=["Turniket"])


def verify_webhook_secret(x_webhook_secret: str = Header(..., alias="X-Webhook-Secret")) -> None:
    if x_webhook_secret != settings.webhook_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Noto'g'ri webhook kaliti")


@router.post("/turnstile", response_model=TurnstileEventResponse)
async def receive_turnstile_event(
    event: TurnstileEvent,
    _: None = Depends(verify_webhook_secret),
    db: AsyncSession = Depends(get_db),
) -> TurnstileEventResponse:
    """
    Turniket qurilmasidan keladigan kirish/chiqish voqealarini qabul qiladi.

    Turniket tizimi har safar o'quvchi karta/RFID skanerlaganda
    ushbu endpointga POST so'rov yuboradi.
    """
    service = AttendanceService()
    attendance, message, sent_count, student_name = await service.process_turnstile_event(db, event)

    if not attendance:
        return TurnstileEventResponse(success=False, message=message, notifications_sent=0)

    return TurnstileEventResponse(
        success=True,
        message=message,
        event_id=attendance.id,
        student_name=student_name,
        notifications_sent=sent_count,
    )
