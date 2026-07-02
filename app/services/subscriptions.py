import calendar
from datetime import datetime, timedelta, timezone

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


def has_accepted_consent(parent: Parent) -> bool:
    return parent.consent_accepted_at is not None


def accept_consent(db: Session, parent: Parent, now: datetime | None = None) -> Parent:
    accepted_at = now or utc_now()
    if parent.consent_accepted_at is None:
        parent.consent_accepted_at = accepted_at
    if parent.trial_expires_at is None:
        parent.trial_expires_at = accepted_at + timedelta(days=settings.free_trial_days)
    db.commit()
    db.refresh(parent)
    return parent


def get_trial_expires_at(parent: Parent) -> datetime | None:
    if parent.trial_expires_at is None:
        return None
    return ensure_aware(parent.trial_expires_at)


def is_trial_active(parent: Parent, now: datetime | None = None) -> bool:
    trial_expires_at = get_trial_expires_at(parent)
    if trial_expires_at is None:
        return False
    return trial_expires_at >= (now or utc_now())


def is_subscription_active(db: Session, parent_id: int, now: datetime | None = None) -> bool:
    expires_at = get_subscription_expires_at(db, parent_id)
    if expires_at is None:
        return False
    return expires_at >= (now or utc_now())


def is_access_active(db: Session, parent: Parent, now: datetime | None = None) -> bool:
    current_time = now or utc_now()
    return is_trial_active(parent, current_time) or is_subscription_active(db, parent.id, current_time)


def get_access_expires_at(db: Session, parent: Parent) -> datetime | None:
    trial_expires_at = get_trial_expires_at(parent)
    subscription_expires_at = get_subscription_expires_at(db, parent.id)
    dates = [value for value in [trial_expires_at, subscription_expires_at] if value is not None]
    if not dates:
        return None
    return max(dates)


def format_subscription_status(db: Session, parent_id: int) -> str:
    parent = db.query(Parent).filter(Parent.id == parent_id).first()
    if parent is None:
        return "Ota-ona topilmadi."

    if not has_accepted_consent(parent):
        return "Rozilik shartnomasi hali tasdiqlanmagan. Avval /rozilik buyrug'idan foydalaning."

    trial_expires_at = get_trial_expires_at(parent)
    if trial_expires_at and trial_expires_at >= utc_now():
        return f"3 kunlik bepul sinov faol. Tugash sanasi: {trial_expires_at.strftime('%d.%m.%Y')}"

    expires_at = get_subscription_expires_at(db, parent_id)
    if expires_at is None:
        return "Bepul sinov muddati tugagan. Xabar olish uchun obuna talab qilinadi."

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
