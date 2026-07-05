from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.attendance import AttendanceEvent
from app.models.device import Device
from app.models.parent import Parent, StudentParent
from app.models.student import Student
from app.schemas import TurnstileEvent
from app.services.subscription import SubscriptionService
from app.services.telegram import TelegramService


class AttendanceService:
    def __init__(self) -> None:
        self.tg = TelegramService()

    async def process(self, db: AsyncSession, ev: TurnstileEvent) -> tuple:
        r = await db.execute(
            select(Student).options(selectinload(Student.school))
            .where(Student.card_id == ev.card_id, Student.is_active.is_(True))
        )
        student = r.scalar_one_or_none()
        if not student:
            return None, f"Karta topilmadi: {ev.card_id}", 0, None

        r = await db.execute(select(Device).where(Device.device_code == ev.device_code, Device.is_active.is_(True)))
        device = r.scalar_one_or_none()
        direction = device.direction if device and device.direction in ("in", "out") else ev.direction.value

        att = AttendanceEvent(
            student_id=student.id, device_id=device.id if device else None,
            direction=direction, card_id=ev.card_id,
            event_time=ev.event_time or datetime.now(timezone.utc),
        )
        db.add(att)
        await db.flush()

        settings = await SubscriptionService.get_settings(db)
        r = await db.execute(
            select(Parent).join(StudentParent).where(
                StudentParent.student_id == student.id,
                Parent.is_active.is_(True), Parent.telegram_chat_id.is_not(None),
            )
        )
        parents = list(r.scalars().all())
        msg = self.tg.attendance_msg(student, direction, att.event_time, device)
        sent = 0
        for p in parents:
            if SubscriptionService.status(p, settings)["notify"]:
                if await self.tg.send(p.telegram_chat_id, msg):  # type: ignore
                    sent += 1
        att.notified = sent > 0
        await db.commit()
        name = f"{student.first_name} {student.last_name}"
        return att, f"{name} - {direction} qayd etildi", sent, name
