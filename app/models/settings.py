from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AppSettings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    trial_days: Mapped[int] = mapped_column(Integer, default=3)
    subscription_price: Mapped[int] = mapped_column(Integer, default=30000)
    subscription_period_days: Mapped[int] = mapped_column(Integer, default=30)
    currency: Mapped[str] = mapped_column(String(10), default="UZS")
    payment_card_number: Mapped[str | None] = mapped_column(String(30))
    payment_card_holder: Mapped[str | None] = mapped_column(String(100))
    payment_click_link: Mapped[str | None] = mapped_column(Text)
    payment_info: Mapped[str | None] = mapped_column(Text, default="To'lovdan keyin admin obunani faollashtiradi.")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
