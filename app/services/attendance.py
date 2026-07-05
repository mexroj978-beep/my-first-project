from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.attendance import AttendanceEvent
from app.models.device import Device
from app.models.parent import Parent, StudentParent
from app.models.student import Student
from app.schemas import Direction, TurnstileEvent
from app.services.subscription import SubscriptionService
from app.services.telegram import TelegramNotifier


class AttendanceService:
    def __init__(self, notifier: TelegramNotifier | None = None) -> None:
        self.notifier = notifier or TelegramNotifier()

    async def process_turnstile_event(
        self,
        session: AsyncSession,
        event: TurnstileEvent,
    ) -> tuple[AttendanceEvent | None, str, int, str | None]:
        student = await self._get_student_by_card(session, event.card_id)
        if not student:
            return None, f"Karta topilmadi: {event.card_id}", 0, None

        device = await self._get_device(session, event.device_code)
        direction = self._resolve_direction(event.direction.value, device)

        event_time = event.event_time or datetime.now(timezone.utc)
        attendance = AttendanceEvent(
            student_id=student.id,
            device_id=device.id if device else None,
            direction=direction,
            card_id=event.card_id,
            event_time=event_time,
        )
        session.add(attendance)
        await session.flush()

        parents = await self._get_active_parents(session, student.id)
        settings = await SubscriptionService.get_settings(session)
        sent_count = await self._notify_parents(student, parents, direction, event_time, device, settings)

        attendance.notified = sent_count > 0
        await session.commit()
        await session.refresh(attendance)

        student_name = f"{student.first_name} {student.last_name}"
        return attendance, f"{student_name} - {direction} qayd etildi", sent_count, student_name

    async def _get_student_by_card(self, session: AsyncSession, card_id: str) -> Student | None:
        result = await session.execute(
            select(Student)
            .options(selectinload(Student.school))
            .where(Student.card_id == card_id, Student.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def _get_device(self, session: AsyncSession, device_code: str) -> Device | None:
        result = await session.execute(
            select(Device).where(Device.device_code == device_code, Device.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    def _resolve_direction(self, event_direction: str, device: Device | None) -> str:
        if device and device.direction in {"in", "out"}:
            return device.direction
        return event_direction

    async def _get_active_parents(self, session: AsyncSession, student_id: int) -> list[Parent]:
        result = await session.execute(
            select(Parent)
            .join(StudentParent, StudentParent.parent_id == Parent.id)
            .where(
                StudentParent.student_id == student_id,
                Parent.is_active.is_(True),
                Parent.telegram_chat_id.is_not(None),
            )
        )
        return list(result.scalars().all())

    async def _notify_parents(
        self,
        student: Student,
        parents: list[Parent],
        direction: str,
        event_time: datetime,
        device: Device | None,
        settings,
    ) -> int:
        if not parents:
            return 0

        message = self.notifier.build_attendance_message(
            student=student,
            direction=direction,
            event_time=event_time,
            device=device,
        )

        sent = 0
        for parent in parents:
            if not SubscriptionService.can_receive_notifications(parent, settings):
                continue
            if parent.telegram_chat_id and await self.notifier.send_message(parent.telegram_chat_id, message):
                sent += 1
        return sent
