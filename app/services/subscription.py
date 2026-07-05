from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parent import Parent
from app.models.settings import AppSettings


class SubscriptionService:
    @staticmethod
    async def get_settings(db: AsyncSession) -> AppSettings:
        s = await db.get(AppSettings, 1)
        if not s:
            s = AppSettings(id=1)
            db.add(s)
            await db.commit()
            await db.refresh(s)
        return s

    @staticmethod
    def status(parent: Parent, settings: AppSettings) -> dict:
        now = datetime.now(timezone.utc)
        if not parent.telegram_chat_id:
            return {"code": "waiting", "label": "Kutilmoqda", "notify": False}
        if parent.subscription_until and parent.subscription_until > now:
            d = (parent.subscription_until - now).days
            return {"code": "active", "label": f"Obuna faol ({d} kun)", "notify": True}
        if parent.bot_registered_at:
            end = parent.bot_registered_at + timedelta(days=settings.trial_days)
            if now < end:
                d = (end - now).days + 1
                return {"code": "trial", "label": f"Bepul sinov ({d} kun)", "notify": True}
            return {"code": "expired", "label": "Obuna tugagan", "notify": False}
        return {"code": "waiting", "label": "Kutilmoqda", "notify": False}

    @staticmethod
    async def activate(db: AsyncSession, parent: Parent, settings: AppSettings, months: int = 1) -> None:
        now = datetime.now(timezone.utc)
        period = timedelta(days=settings.subscription_period_days * months)
        base = parent.subscription_until if parent.subscription_until and parent.subscription_until > now else now
        parent.subscription_until = base + period
        if not parent.bot_registered_at:
            parent.bot_registered_at = now
        await db.commit()
