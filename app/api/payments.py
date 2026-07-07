from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.services.payment import PaymentService
from app.services.payment_lookup import get_order_by_ref

router = APIRouter(tags=["To'lov"])
wh = APIRouter(prefix="/webhooks", tags=["To'lov"])


@wh.post("/payment/click")
async def click_hook(request: Request, db: AsyncSession = Depends(get_db)):
    return await PaymentService().click_webhook(db, dict(await request.form()))


def _pay_html(order, cfg, url: str) -> str:
    demo = (
        f"""<form method="POST" action="/pay/{order.access_token}/done" style="margin-top:20px">
      <button style="padding:15px 40px;background:#2563eb;color:#fff;border:none;border-radius:8px;font-size:16px;cursor:pointer">
        💳 To'lov qildim</button></form>"""
        if settings.payment_demo_mode
        else ""
    )
    card = ""
    if cfg.payment_card_number:
        holder = f"<p>👤 {cfg.payment_card_holder}</p>" if cfg.payment_card_holder else ""
        card = f'<p style="font-size:18px">🏦 Karta: <b style="letter-spacing:1px">{cfg.payment_card_number}</b></p>{holder}'
    show_click = cfg.payment_click_link or settings.click_service_id
    click = (
        f'<a href="{url}" style="display:inline-block;padding:15px 40px;background:#00A651;color:#fff;'
        f'text-decoration:none;border-radius:8px;margin:10px">Click orqali to\'lash</a>'
        if show_click
        else ""
    )
    info = f'<p style="color:#666">{cfg.payment_info}</p>' if cfg.payment_info else ""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>To'lov</title></head><body style="font-family:sans-serif;text-align:center;padding:40px">
    <h1>💳 Obuna to'lovi</h1><p style="font-size:28px;font-weight:bold">{order.amount:,} {order.currency}</p>
    {card}{click}{demo}{info}<p style="color:#666;margin-top:20px">To'lovdan keyin obuna avtomatik yoqiladi</p></body></html>"""


@router.get("/pay/{ref}", response_class=HTMLResponse)
async def pay_page(ref: str, db: AsyncSession = Depends(get_db)):
    order = await get_order_by_ref(db, ref)
    if not order:
        return HTMLResponse("<h1>Topilmadi</h1>", 404)
    if order.status == "paid":
        return HTMLResponse("<h1>✅ To'lov qilingan</h1><p>Botga qayting</p>")
    ps = PaymentService()
    from app.services.subscription import SubscriptionService as SS

    cfg = await SS.get_settings(db)
    url = ps.pay_url(order, cfg)
    return HTMLResponse(_pay_html(order, cfg, url))


@router.post("/pay/{ref}/done", response_class=HTMLResponse)
async def pay_done(ref: str, db: AsyncSession = Depends(get_db)):
    order = await get_order_by_ref(db, ref)
    if not order:
        raise HTTPException(404)
    await PaymentService().complete(db, order, f"demo-{order.id}")
    return HTMLResponse("<h1>✅ Obuna faollashtirildi!</h1><p>Telegram botga qayiting</p>")
