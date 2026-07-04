from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    class_name: Mapped[str] = mapped_column(String(50), nullable=False)
    card_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    school: Mapped["School"] = relationship(back_populates="students")
    parents: Mapped[list["Parent"]] = relationship(
        secondary="student_parents",
        back_populates="students",
    )
    attendance_events: Mapped[list["AttendanceEvent"]] = relationship(back_populates="student")


from app.models.attendance import AttendanceEvent  # noqa: E402
from app.models.parent import Parent  # noqa: E402
from app.models.school import School  # noqa: E402
