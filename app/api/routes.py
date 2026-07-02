from datetime import datetime, timezone

from aiogram import Bot
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Student
from app.schemas import StudentCreate, StudentResponse, TurnstileEvent, TurnstileEventResponse
from app.services.attendance import generate_registration_code, process_turnstile_event

router = APIRouter(prefix="/api", tags=["api"])


def verify_turnstile_key(x_api_key: str = Header(...)) -> None:
    if x_api_key != settings.turnstile_api_key:
        raise HTTPException(status_code=401, detail="Noto'g'ri API kalit")


def verify_admin_key(x_admin_key: str = Header(...)) -> None:
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Noto'g'ri admin kalit")


@router.post("/turnstile/event", response_model=TurnstileEventResponse)
async def receive_turnstile_event(
    event: TurnstileEvent,
    db: Session = Depends(get_db),
    _: None = Depends(verify_turnstile_key),
) -> TurnstileEventResponse:
    """
    Tirniket tizimidan keladigan voqealarni qabul qiladi.

    Ko'pchilik tirniket tizimlari HTTP POST webhook yuboradi.
    Ushbu endpointga quyidagi formatda so'rov yuboring:

    ```json
    {
        "card_id": "1234567890",
        "event_type": "enter",
        "event_time": "2026-07-02T08:30:00",
        "device_id": "gate-01"
    }
    ```
    """
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=503, detail="Telegram bot sozlanmagan")

    bot = Bot(token=settings.telegram_bot_token)
    try:
        success, message, student, sent = await process_turnstile_event(
            db=db,
            bot=bot,
            card_id=event.card_id,
            event_type=event.event_type,
            event_time=event.event_time,
            device_id=event.device_id,
        )
    finally:
        await bot.session.close()

    return TurnstileEventResponse(
        success=success,
        message=message,
        student_name=student.full_name if student else None,
        notifications_sent=sent,
    )


@router.post("/admin/students", response_model=StudentResponse)
def create_student(
    data: StudentCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_key),
) -> Student:
    """Yangi o'quvchini tizimga qo'shish (admin uchun)."""
    existing = db.query(Student).filter(Student.card_id == data.card_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu karta allaqachon ro'yxatdan o'tgan")

    code = data.registration_code or generate_registration_code()
    if db.query(Student).filter(Student.registration_code == code.upper()).first():
        raise HTTPException(status_code=400, detail="Ro'yxatdan o'tish kodi band")

    student = Student(
        full_name=data.full_name,
        class_name=data.class_name,
        card_id=data.card_id,
        registration_code=code.upper(),
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.get("/admin/students", response_model=list[StudentResponse])
def list_students(
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_key),
) -> list[Student]:
    return db.query(Student).order_by(Student.class_name, Student.full_name).all()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}
