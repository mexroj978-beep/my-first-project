import calendar
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Parent, Payment


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def get_subscription_expires_at(db: Session, parent_id: int) -> datetime | None:
    payment = (
        db.query(Payment)
        .filter(Payment.parent_id == parent_id)
        .order_by(Payment.expires_at.desc())
        .first()
    )
    if payment is None:
        return None
    return ensure_aware(payment.expires_at)


def is_subscription_active(db: Session, parent_id: int, now: datetime | None = None) -> bool:
    expires_at = get_subscription_expires_at(db, parent_id)
    if expires_at is None:
        return False
    return expires_at >= (now or utc_now())


def format_subscription_status(db: Session, parent_id: int) -> str:
    expires_at = get_subscription_expires_at(db, parent_id)
    if expires_at is None:
        return "Obuna hali faollashtirilmagan."

    expires_at = ensure_aware(expires_at)
    if expires_at >= utc_now():
        return f"Obuna faol. Amal qilish muddati: {expires_at.strftime('%d.%m.%Y')}"
    return f"Obuna muddati tugagan: {expires_at.strftime('%d.%m.%Y')}"


def create_payment(
    db: Session,
    parent: Parent,
    months: int = 1,
    amount_som: int | None = None,
    paid_at: datetime | None = None,
    note: str | None = None,
) -> Payment:
    now = paid_at or utc_now()
    latest_expires_at = get_subscription_expires_at(db, parent.id)
    starts_at = latest_expires_at if latest_expires_at and latest_expires_at > now else now
    expires_at = add_months(starts_at, months)

    payment = Payment(
        parent_id=parent.id,
        amount_som=amount_som if amount_som is not None else settings.monthly_subscription_amount * months,
        months=months,
        paid_at=now,
        starts_at=starts_at,
        expires_at=expires_at,
        note=note,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment
