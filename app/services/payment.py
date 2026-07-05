import hashlib
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.parent import Parent
from app.models.payment import PaymentOrder
from app.models.settings import AppSettings
from app.services.subscription import SubscriptionService
from app.services.telegram import TelegramNotifier

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, notifier: TelegramNotifier | None = None) -> None:
        self.notifier = notifier or TelegramNotifier()

    async def create_order(self, session: AsyncSession, parent: Parent, app_settings: AppSettings) -> PaymentOrder:
        order = PaymentOrder(
            parent_id=parent.id,
            amount=app_settings.subscription_price,
            currency=app_settings.currency,
            status="pending",
            provider="click" if settings.click_service_id else "demo",
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        return order

    def get_payment_url(self, order: PaymentOrder) -> str:
        if settings.click_service_id and settings.click_merchant_id:
            return (
                f"https://my.click.uz/services/pay"
                f"?service_id={settings.click_service_id}"
                f"&merchant_id={settings.click_merchant_id}"
                f"&amount={order.amount}"
                f"&transaction_param={order.id}"
            )
        base = settings.app_base_url.rstrip("/")
        return f"{base}/pay/{order.id}"

    async def complete_order(
        self,
        session: AsyncSession,
        order: PaymentOrder,
        external_id: str | None = None,
    ) -> Parent:
        if order.status == "paid":
            order_parent = await session.get(Parent, order.parent_id)
            return order_parent  # type: ignore

        order.status = "paid"
        order.paid_at = datetime.now(timezone.utc)
        if external_id:
            order.external_id = external_id

        parent = await session.get(Parent, order.parent_id)
        if not parent:
            raise ValueError("Ota-ona topilmadi")

        app_settings = await SubscriptionService.get_settings(session)
        await SubscriptionService.activate_subscription(session, parent, app_settings, months=1)
        await session.commit()
        await session.refresh(parent)

        if parent.telegram_chat_id:
            status = SubscriptionService.get_status(parent, app_settings)
            await self.notifier.send_message(
                parent.telegram_chat_id,
                f"✅ <b>To'lov qabul qilindi!</b>\n\n"
                f"💰 Summa: {order.amount:,} {order.currency}\n"
                f"📊 Obuna: <b>{status['label']}</b>\n\n"
                f"Endi farzandingiz haqida xabarlar keladi.",
            )

        logger.info("To'lov tasdiqlandi: order=%s parent=%s", order.id, parent.id)
        return parent

    async def get_order(self, session: AsyncSession, order_id: int) -> PaymentOrder | None:
        return await session.get(PaymentOrder, order_id)

    def verify_click_sign(
        self,
        click_trans_id: str,
        service_id: str,
        merchant_trans_id: str,
        amount: str,
        action: str,
        sign_time: str,
        sign_string: str,
    ) -> bool:
        if not settings.click_secret_key:
            return settings.payment_demo_mode
        raw = f"{click_trans_id}{service_id}{settings.click_secret_key}{merchant_trans_id}{amount}{action}{sign_time}"
        expected = hashlib.md5(raw.encode()).hexdigest()
        return expected == sign_string

    async def handle_click_webhook(self, session: AsyncSession, data: dict) -> dict:
        action = int(data.get("action", -1))
        merchant_trans_id = str(data.get("merchant_trans_id", ""))
        click_trans_id = str(data.get("click_trans_id", ""))
        amount = str(data.get("amount", ""))
        service_id = str(data.get("service_id", ""))
        sign_time = str(data.get("sign_time", ""))
        sign_string = str(data.get("sign_string", ""))

        try:
            order_id = int(merchant_trans_id)
        except ValueError:
            return {"error": -8, "error_note": "Noto'g'ri buyurtma ID"}

        order = await self.get_order(session, order_id)
        if not order:
            return {"error": -5, "error_note": "Buyurtma topilmadi"}

        if not self.verify_click_sign(
            click_trans_id, service_id, merchant_trans_id, amount, str(action), sign_time, sign_string
        ):
            return {"error": -1, "error_note": "Imzo noto'g'ri"}

        if int(float(amount)) != order.amount:
            return {"error": -2, "error_note": "Summa noto'g'ri"}

        if action == 0:
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_prepare_id": order.id,
                "error": 0,
                "error_note": "Success",
            }

        if action == 1:
            if order.status == "paid":
                return {
                    "click_trans_id": click_trans_id,
                    "merchant_trans_id": merchant_trans_id,
                    "merchant_confirm_id": order.id,
                    "error": 0,
                    "error_note": "Success",
                }
            await self.complete_order(session, order, external_id=click_trans_id)
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_confirm_id": order.id,
                "error": 0,
                "error_note": "Success",
            }

        return {"error": -3, "error_note": "Noto'g'ri action"}
