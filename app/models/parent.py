from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Parent(Base):
    __tablename__ = "parents"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True)
    telegram_username: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    students: Mapped[list["Student"]] = relationship(
        secondary="student_parents",
        back_populates="parents",
    )


class StudentParent(Base):
    __tablename__ = "student_parents"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    parent_id: Mapped[int] = mapped_column(ForeignKey("parents.id"), nullable=False)
    relation: Mapped[str] = mapped_column(String(50), default="ota-ona")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


from app.models.student import Student  # noqa: E402
