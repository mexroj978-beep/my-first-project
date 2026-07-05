from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Direction(str, Enum):
    IN = "in"
    OUT = "out"


# --- Turniket ---
class TurnstileEvent(BaseModel):
    card_id: str
    device_code: str
    direction: Direction
    event_time: datetime | None = None


class TurnstileResponse(BaseModel):
    success: bool
    message: str
    event_id: int | None = None
    student_name: str | None = None
    notifications_sent: int = 0


# --- Maktab ---
class SchoolCreate(BaseModel):
    name: str
    address: str | None = None


class SchoolOut(BaseModel):
    id: int
    name: str
    address: str | None
    model_config = {"from_attributes": True}


# --- O'quvchi ---
class StudentCreate(BaseModel):
    school_id: int
    first_name: str
    last_name: str
    class_name: str
    card_id: str


class StudentUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    class_name: str | None = None
    card_id: str | None = None
    school_id: int | None = None
    is_active: bool | None = None


class StudentOut(BaseModel):
    id: int
    school_id: int
    first_name: str
    last_name: str
    class_name: str
    card_id: str
    is_active: bool
    model_config = {"from_attributes": True}


# --- Ota-ona ---
class ParentCreate(BaseModel):
    full_name: str
    phone: str | None = None
    student_ids: list[int] = Field(default_factory=list)


class ParentUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    student_ids: list[int] | None = None
    is_active: bool | None = None


class ParentOut(BaseModel):
    id: int
    full_name: str
    phone: str | None
    telegram_chat_id: int | None
    is_active: bool
    subscription_status: str = "Kutilmoqda"
    model_config = {"from_attributes": True}


# --- Turniket qurilma ---
class DeviceCreate(BaseModel):
    school_id: int
    device_code: str
    name: str
    location: str = "Asosiy kirish"
    direction: Direction = Direction.IN


class DeviceOut(BaseModel):
    id: int
    school_id: int
    device_code: str
    name: str
    location: str
    direction: str
    is_active: bool
    model_config = {"from_attributes": True}


# --- Davomat ---
class AttendanceOut(BaseModel):
    id: int
    student_id: int
    direction: str
    card_id: str
    event_time: datetime
    notified: bool
    model_config = {"from_attributes": True}


# --- Obuna ---
class SettingsOut(BaseModel):
    trial_days: int
    subscription_price: int
    subscription_period_days: int
    currency: str
    payment_info: str | None
    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    trial_days: int | None = None
    subscription_price: int | None = None
    subscription_period_days: int | None = None
    currency: str | None = None
    payment_info: str | None = None


class ActivateSub(BaseModel):
    months: int = Field(default=1, ge=1, le=12)
