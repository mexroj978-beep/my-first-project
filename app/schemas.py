from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TurnstileEvent(BaseModel):
    card_id: str = Field(..., description="RFID karta yoki tirniket identifikatori")
    event_type: Literal["enter", "exit"] = Field(..., description="Kirish yoki chiqish")
    event_time: datetime | None = Field(None, description="Voqea vaqti (bo'sh bo'lsa — hozirgi vaqt)")
    device_id: str | None = Field(None, description="Tirniket qurilma ID")


class StudentCreate(BaseModel):
    full_name: str
    class_name: str
    card_id: str
    registration_code: str | None = None


class StudentResponse(BaseModel):
    id: int
    full_name: str
    class_name: str
    card_id: str
    registration_code: str

    model_config = {"from_attributes": True}


class TurnstileEventResponse(BaseModel):
    success: bool
    message: str
    student_name: str | None = None
    notifications_sent: int = 0


class LinkedStudentResponse(BaseModel):
    id: int
    full_name: str
    class_name: str


class ParentAdminResponse(BaseModel):
    id: int
    telegram_id: int
    full_name: str | None = None
    phone: str | None = None
    created_at: datetime
    subscription_active: bool
    subscription_expires_at: datetime | None = None
    children: list[LinkedStudentResponse]


class PaymentCreate(BaseModel):
    parent_id: int | None = Field(None, description="Ota-ona ID raqami")
    telegram_id: int | None = Field(None, description="Ota-onaning Telegram ID raqami")
    months: int = Field(1, ge=1, le=24, description="Necha oyga obuna uzaytiriladi")
    amount_som: int | None = Field(None, ge=0, description="To'langan summa, so'm")
    note: str | None = Field(None, description="To'lov izohi")


class PaymentResponse(BaseModel):
    id: int
    parent_id: int
    telegram_id: int
    parent_name: str | None = None
    amount_som: int
    months: int
    paid_at: datetime
    starts_at: datetime
    expires_at: datetime
    note: str | None = None
