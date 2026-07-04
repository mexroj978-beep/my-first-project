from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings
from app.models.device import Device
from app.models.student import Student


class TelegramNotifier:
    def __init__(self, bot_token: str | None = None) -> None:
        self.bot_token = bot_token or settings.telegram_bot_token
        self._bot = None

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token)

    def _get_bot(self):
        if not self.is_configured:
            return None
        if self._bot is None:
            from telegram import Bot

            self._bot = Bot(token=self.bot_token)
        return self._bot

    async def send_message(self, chat_id: int, text: str) -> bool:
        bot = self._get_bot()
        if not bot:
            return False
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
            return True
        except Exception:
            return False

    def build_attendance_message(
        self,
        student: Student,
        direction: str,
        event_time: datetime,
        device: Device | None = None,
    ) -> str:
        tz = ZoneInfo(settings.timezone)
        local_time = event_time.astimezone(tz)
        time_str = local_time.strftime("%H:%M")
        date_str = local_time.strftime("%d.%m.%Y")

        if direction == "in":
            action = "maktabga <b>kirdi</b>"
            emoji = "🏫✅"
        else:
            action = "maktabdan <b>chiqdi</b>"
            emoji = "🚪👋"

        location = device.location if device else "Asosiy kirish"
        school_name = student.school.name if student.school else "Maktab"

        return (
            f"{emoji} <b>Farzandingiz haqida xabar</b>\n\n"
            f"👤 <b>{student.first_name} {student.last_name}</b>\n"
            f"📚 Sinf: {student.class_name}\n"
            f"🏫 {school_name}\n\n"
            f"⏰ Vaqt: {time_str} ({date_str})\n"
            f"📍 Joy: {location}\n"
            f"📌 Farzandingiz {action}."
        )
