from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings
from app.models.device import Device
from app.models.student import Student


class TelegramService:
    def __init__(self) -> None:
        self._bot = None

    def _bot_instance(self):
        if not settings.telegram_bot_token:
            return None
        if not self._bot:
            from telegram import Bot
            self._bot = Bot(token=settings.telegram_bot_token)
        return self._bot

    async def send(self, chat_id: int, text: str) -> bool:
        bot = self._bot_instance()
        if not bot:
            return False
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
            return True
        except Exception:
            return False

    def attendance_msg(self, student: Student, direction: str, event_time: datetime, device: Device | None) -> str:
        tz = ZoneInfo(settings.timezone)
        t = event_time.astimezone(tz)
        if direction == "in":
            action, emoji = "maktabga <b>kirdi</b>", "🏫✅"
        else:
            action, emoji = "maktabdan <b>chiqdi</b>", "🚪👋"
        loc = device.location if device else "Asosiy kirish"
        school = student.school.name if student.school else "Maktab"
        return (
            f"{emoji} <b>Farzandingiz haqida xabar</b>\n\n"
            f"👤 <b>{student.first_name} {student.last_name}</b>\n"
            f"📚 Sinf: {student.class_name}\n"
            f"🏫 {school}\n\n"
            f"⏰ {t.strftime('%H:%M')} ({t.strftime('%d.%m.%Y')})\n"
            f"📍 {loc}\n"
            f"📌 Farzandingiz {action}."
        )
