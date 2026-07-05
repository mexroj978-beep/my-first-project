from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parent import Parent
from app.models.settings import AppSettings


class SubscriptionService:
    @staticmethod
    async def get_settings(session: AsyncSession) -> AppSettings:
        settings = await session.get(AppSettings, 1)
        if not settings:
            settings = AppSettings(
                id=1,
                trial_days=3,
                subscription_price=30000,
                subscription_period_days=30,
                currency="UZS",
                payment_info="To'lov uchun maktab adminiga murojaat qiling.",
            )
            session.add(settings)
            await session.commit()
            await session.refresh(settings)
        return settings

    @staticmethod
    def get_status(parent: Parent, settings: AppSettings) -> dict:
        now = datetime.now(timezone.utc)

        if not parent.telegram_chat_id:
            return {"code": "waiting", "label": "Kutilmoqda", "can_notify": False}

        if parent.subscription_until and parent.subscription_until > now:
            days_left = (parent.subscription_until - now).days
            return {"code": "active", "label": f"Obuna faol ({days_left} kun)", "can_notify": True}

        if parent.bot_registered_at:
            trial_end = parent.bot_registered_at + timedelta(days=settings.trial_days)
            if now < trial_end:
                days_left = (trial_end - now).days + 1
                return {"code": "trial", "label": f"Bepul sinov ({days_left} kun)", "can_notify": True}
            return {"code": "expired", "label": "Obuna tugagan", "can_notify": False}

        return {"code": "waiting", "label": "Kutilmoqda", "can_notify": False}

    @staticmethod
    def can_receive_notifications(parent: Parent, settings: AppSettings) -> bool:
        return SubscriptionService.get_status(parent, settings)["can_notify"]

    @staticmethod
    async def activate_subscription(
        session: AsyncSession,
        parent: Parent,
        settings: AppSettings,
        months: int = 1,
    ) -> Parent:
        now = datetime.now(timezone.utc)
        period = timedelta(days=settings.subscription_period_days * months)
        base = parent.subscription_until if parent.subscription_until and parent.subscription_until > now else now
        parent.subscription_until = base + period
        if not parent.bot_registered_at:
            parent.bot_registered_at = now
        await session.commit()
        await session.refresh(parent)
        return parent
