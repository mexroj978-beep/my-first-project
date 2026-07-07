import hashlib
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.parent import Parent
from app.models.payment import PaymentOrder
from app.models.settings import AppSettings
from app.services.subscription import SubscriptionService
from app.services.telegram import TelegramService

logger = logging.getLogger(__name__)


from app.utils.security import generate_access_token


class PaymentService:
    def __init__(self) -> None:
        self.tg = TelegramService()

    async def create_order(self, db: AsyncSession, parent: Parent, s: AppSettings) -> PaymentOrder:
        order = PaymentOrder(
            parent_id=parent.id,
            access_token=generate_access_token(),
            amount=s.subscription_price,
            currency=s.currency,
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        return order

    def pay_url(self, order: PaymentOrder, cfg: AppSettings | None = None) -> str:
        if cfg and cfg.payment_click_link:
            return cfg.payment_click_link.strip()
        if settings.click_service_id and settings.click_merchant_id:
            return (
                f"https://my.click.uz/services/pay?service_id={settings.click_service_id}"
                f"&merchant_id={settings.click_merchant_id}&amount={order.amount}"
                f"&transaction_param={order.id}"
            )
        return f"{settings.app_base_url.rstrip('/')}/pay/{order.access_token}"

    def pay_message(self, order: PaymentOrder, cfg: AppSettings) -> str:
        lines = [
            f"💳 <b>Obuna to'lovi</b>",
            f"",
            f"💰 Summa: <b>{order.amount:,} {cfg.currency}</b>",
            f"🧾 Buyurtma: <b>#{order.id}</b>",
        ]
        if cfg.payment_card_number:
            holder = f"\n👤 {cfg.payment_card_holder}" if cfg.payment_card_holder else ""
            lines += ["", "🏦 <b>Karta raqami:</b>", f"<code>{cfg.payment_card_number}</code>{holder}"]
        if cfg.payment_click_link:
            lines += ["", "📱 Quyidagi tugma orqali <b>Click</b> da to'lang."]
        elif cfg.payment_card_number:
            lines += ["", "💬 To'lovdan keyin chek skrinshotini maktab adminiga yuboring."]
        if cfg.payment_info:
            lines += ["", f"ℹ️ {cfg.payment_info}"]
        return "\n".join(lines)

    async def complete(self, db: AsyncSession, order: PaymentOrder, ext_id: str | None = None) -> None:
        if order.status == "paid":
            return
        order.status = "paid"
        order.paid_at = datetime.now(timezone.utc)
        order.external_id = ext_id
        parent = await db.get(Parent, order.parent_id)
        if not parent:
            return
        s = await SubscriptionService.get_settings(db)
        await SubscriptionService.activate(db, parent, s)
        await db.refresh(parent)
        if parent.telegram_chat_id:
            st = SubscriptionService.status(parent, s)
            await self.tg.send(
                parent.telegram_chat_id,
                f"✅ <b>To'lov qabul qilindi!</b>\n\n"
                f"💰 {order.amount:,} {order.currency}\n"
                f"📊 {st['label']}\n\nXabarlar davom etadi.",
            )

    def click_sign_ok(self, click_id, svc_id, merch_id, amount, action, sign_time, sign_string) -> bool:
        if not settings.click_secret_key:
            return settings.payment_demo_mode
        raw = f"{click_id}{svc_id}{settings.click_secret_key}{merch_id}{amount}{action}{sign_time}"
        return hashlib.md5(raw.encode()).hexdigest() == sign_string

    async def click_webhook(self, db: AsyncSession, d: dict) -> dict:
        action = int(d.get("action", -1))
        merch_id = str(d.get("merchant_trans_id", ""))
        try:
            oid = int(merch_id)
        except ValueError:
            return {"error": -8, "error_note": "Noto'g'ri ID"}
        order = await db.get(PaymentOrder, oid)
        if not order:
            return {"error": -5, "error_note": "Topilmadi"}
        if not self.click_sign_ok(
            str(d.get("click_trans_id", "")), str(d.get("service_id", "")),
            merch_id, str(d.get("amount", "")), str(action),
            str(d.get("sign_time", "")), str(d.get("sign_string", "")),
        ):
            return {"error": -1, "error_note": "Imzo xato"}
        if action == 0:
            return {"click_trans_id": d.get("click_trans_id"), "merchant_trans_id": merch_id,
                    "merchant_prepare_id": order.id, "error": 0, "error_note": "Success"}
        if action == 1:
            await self.complete(db, order, str(d.get("click_trans_id", "")))
            return {"click_trans_id": d.get("click_trans_id"), "merchant_trans_id": merch_id,
                    "merchant_confirm_id": order.id, "error": 0, "error_note": "Success"}
        return {"error": -3, "error_note": "Xato action"}
