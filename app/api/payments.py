from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.services.payment import PaymentService

router = APIRouter(tags=["To'lov"])
wh = APIRouter(prefix="/webhooks", tags=["To'lov"])


@wh.post("/payment/click")
async def click_hook(request: Request, db: AsyncSession = Depends(get_db)):
    return await PaymentService().click_webhook(db, dict(await request.form()))


@router.get("/pay/{oid}", response_class=HTMLResponse)
async def pay_page(oid: int, db: AsyncSession = Depends(get_db)):
    from app.models.payment import PaymentOrder
    order = await db.get(PaymentOrder, oid)
    if not order:
        return HTMLResponse("<h1>Topilmadi</h1>", 404)
    if order.status == "paid":
        return HTMLResponse("<h1>✅ To'lov qilingan</h1><p>Botga qayting</p>")
    ps = PaymentService()
    url = ps.pay_url(order)
    demo = f"""<form method="POST" action="/pay/{oid}/done" style="margin-top:20px">
      <button style="padding:15px 40px;background:#2563eb;color:#fff;border:none;border-radius:8px;font-size:16px;cursor:pointer">
        💳 To'lov qildim</button></form>""" if settings.payment_demo_mode else ""
    click = f'<a href="{url}" style="display:inline-block;padding:15px 40px;background:#00A651;color:#fff;text-decoration:none;border-radius:8px">Click orqali to\'lash</a>' if settings.click_service_id else ""
    return HTMLResponse(f"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>To'lov</title></head><body style="font-family:sans-serif;text-align:center;padding:40px">
    <h1>💳 Obuna to'lovi</h1><p style="font-size:28px;font-weight:bold">{order.amount:,} {order.currency}</p>
    {click}{demo}<p style="color:#666;margin-top:20px">To'lovdan keyin obuna avtomatik yoqiladi</p></body></html>""")


@router.post("/pay/{oid}/done", response_class=HTMLResponse)
async def pay_done(oid: int, db: AsyncSession = Depends(get_db)):
    from app.models.payment import PaymentOrder
    order = await db.get(PaymentOrder, oid)
    if not order:
        raise HTTPException(404)
    await PaymentService().complete(db, order, f"demo-{oid}")
    return HTMLResponse("<h1>✅ Obuna faollashtirildi!</h1><p>Telegram botga qayting</p>")
