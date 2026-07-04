from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AttendanceEvent(Base):
    __tablename__ = "attendance_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    device_id: Mapped[int | None] = mapped_column(ForeignKey("devices.id"))
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # in | out
    card_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    notified: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    student: Mapped["Student"] = relationship(back_populates="attendance_events")
    device: Mapped["Device | None"] = relationship(back_populates="attendance_events")


from app.models.device import Device  # noqa: E402
from app.models.student import Student  # noqa: E402
