"""To'lov buyurtmasini token yoki eski raqamli ID bo'yicha topish."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import PaymentOrder


async def get_order_by_ref(db: AsyncSession, ref: str) -> PaymentOrder | None:
    if ref.isdigit():
        return await db.get(PaymentOrder, int(ref))
    r = await db.execute(select(PaymentOrder).where(PaymentOrder.access_token == ref))
    return r.scalar_one_or_none()
