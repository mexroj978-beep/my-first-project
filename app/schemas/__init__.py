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


class StudentUpdate(BaseModel):
    school_id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    class_name: str | None = None
    card_id: str | None = None
    is_active: bool | None = None


class ParentUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    is_active: bool | None = None
    student_ids: list[int] | None = None


class ParentResponse(BaseModel):
    id: int
    full_name: str
    phone: str | None
    telegram_chat_id: int | None
    is_active: bool
    bot_registered_at: datetime | None = None
    subscription_until: datetime | None = None
    subscription_status: str | None = None

    model_config = {"from_attributes": True}


class SubscriptionSettingsResponse(BaseModel):
    trial_days: int
    subscription_price: int
    subscription_period_days: int
    currency: str
    payment_info: str | None

    model_config = {"from_attributes": True}


class SubscriptionSettingsUpdate(BaseModel):
    trial_days: int | None = None
    subscription_price: int | None = None
    subscription_period_days: int | None = None
    currency: str | None = None
    payment_info: str | None = None


class ActivateSubscription(BaseModel):
    months: int = Field(default=1, ge=1, le=12)


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
