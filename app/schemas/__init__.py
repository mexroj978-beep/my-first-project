from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Direction(str, Enum):
    IN = "in"
    OUT = "out"


class TurnstileEvent(BaseModel):
    """Turniket qurilmasidan keladigan webhook ma'lumoti."""

    card_id: str = Field(..., description="Karta/RFID identifikatori")
    device_code: str = Field(..., description="Turniket qurilma kodi")
    direction: Direction = Field(..., description="in - kirish, out - chiqish")
    event_time: datetime | None = Field(None, description="Voqea vaqti (ixtiyoriy)")


class TurnstileEventResponse(BaseModel):
    success: bool
    message: str
    event_id: int | None = None
    student_name: str | None = None
    notifications_sent: int = 0


class SchoolCreate(BaseModel):
    name: str
    address: str | None = None


class SchoolResponse(BaseModel):
    id: int
    name: str
    address: str | None

    model_config = {"from_attributes": True}


class StudentCreate(BaseModel):
    school_id: int
    first_name: str
    last_name: str
    class_name: str
    card_id: str


class StudentResponse(BaseModel):
    id: int
    school_id: int
    first_name: str
    last_name: str
    class_name: str
    card_id: str
    is_active: bool

    model_config = {"from_attributes": True}


class ParentCreate(BaseModel):
    full_name: str
    phone: str | None = None
    student_ids: list[int] = Field(default_factory=list)


class ParentResponse(BaseModel):
    id: int
    full_name: str
    phone: str | None
    telegram_chat_id: int | None
    is_active: bool

    model_config = {"from_attributes": True}


class DeviceCreate(BaseModel):
    school_id: int
    device_code: str
    name: str
    location: str = "Asosiy kirish"
    direction: Direction = Direction.IN


class DeviceResponse(BaseModel):
    id: int
    school_id: int
    device_code: str
    name: str
    location: str
    direction: str
    is_active: bool

    model_config = {"from_attributes": True}


class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    direction: str
    card_id: str
    event_time: datetime
    notified: bool

    model_config = {"from_attributes": True}


class LinkParentStudent(BaseModel):
    parent_id: int
    student_id: int
    relation: str = "ota-ona"
