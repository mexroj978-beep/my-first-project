import secrets
import string
from datetime import datetime, timezone

from aiogram import Bot
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AttendanceEvent, Parent, ParentStudent, Student


def generate_registration_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def get_student_by_card(db: Session, card_id: str) -> Student | None:
    return db.query(Student).filter(Student.card_id == card_id).first()


def get_student_by_code(db: Session, code: str) -> Student | None:
    return db.query(Student).filter(Student.registration_code == code.upper()).first()


def get_or_create_parent(db: Session, telegram_id: int, full_name: str | None = None) -> Parent:
    parent = db.query(Parent).filter(Parent.telegram_id == telegram_id).first()
    if parent is None:
        parent = Parent(telegram_id=telegram_id, full_name=full_name)
        db.add(parent)
        db.commit()
        db.refresh(parent)
    elif full_name and not parent.full_name:
        parent.full_name = full_name
        db.commit()
    return parent


def link_parent_to_student(db: Session, parent: Parent, student: Student) -> bool:
    existing = (
        db.query(ParentStudent)
        .filter(ParentStudent.parent_id == parent.id, ParentStudent.student_id == student.id)
        .first()
    )
    if existing:
        return False
    db.add(ParentStudent(parent_id=parent.id, student_id=student.id))
    db.commit()
    return True


def get_parents_for_student(db: Session, student_id: int) -> list[Parent]:
    return (
        db.query(Parent)
        .join(ParentStudent, ParentStudent.parent_id == Parent.id)
        .filter(ParentStudent.student_id == student_id)
        .all()
    )


def format_notification(student: Student, event_type: str, event_time: datetime) -> str:
    action = "maktabga kirdi" if event_type == "enter" else "maktabdan chiqdi"
    time_str = event_time.strftime("%H:%M")
    date_str = event_time.strftime("%d.%m.%Y")

    return (
        f"📢 <b>{settings.school_name}</b>\n\n"
        f"👤 <b>{student.full_name}</b> ({student.class_name}-sinf)\n"
        f"{'✅' if event_type == 'enter' else '🚪'} Farzandingiz {action}.\n\n"
        f"🕐 Vaqt: {time_str}\n"
        f"📅 Sana: {date_str}"
    )


async def send_attendance_notifications(
    db: Session,
    bot: Bot,
    student: Student,
    event_type: str,
    event_time: datetime,
    card_id: str,
    device_id: str | None = None,
) -> int:
    parents = get_parents_for_student(db, student.id)
    message = format_notification(student, event_type, event_time)
    sent_count = 0

    for parent in parents:
        try:
            await bot.send_message(chat_id=parent.telegram_id, text=message, parse_mode="HTML")
            sent_count += 1
        except Exception:
            pass

    event = AttendanceEvent(
        student_id=student.id,
        event_type=event_type,
        card_id=card_id,
        device_id=device_id,
        event_time=event_time,
        notified=sent_count > 0,
    )
    db.add(event)
    db.commit()
    return sent_count


async def process_turnstile_event(
    db: Session,
    bot: Bot,
    card_id: str,
    event_type: str,
    event_time: datetime | None = None,
    device_id: str | None = None,
) -> tuple[bool, str, Student | None, int]:
    student = get_student_by_card(db, card_id)
    if student is None:
        return False, f"Karta topilmadi: {card_id}", None, 0

    when = event_time or datetime.now(timezone.utc)
    sent = await send_attendance_notifications(db, bot, student, event_type, when, card_id, device_id)
    action = "kirdi" if event_type == "enter" else "chiqdi"
    return True, f"{student.full_name} maktabga {action}", student, sent
