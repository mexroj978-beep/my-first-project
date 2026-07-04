from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), nullable=False)
    device_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str] = mapped_column(String(200), default="Asosiy kirish")
    direction: Mapped[str] = mapped_column(String(10), default="in")  # in | out | both
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    school: Mapped["School"] = relationship(back_populates="devices")
    attendance_events: Mapped[list["AttendanceEvent"]] = relationship(back_populates="device")


from app.models.attendance import AttendanceEvent  # noqa: E402
from app.models.school import School  # noqa: E402
