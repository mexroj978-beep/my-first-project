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
