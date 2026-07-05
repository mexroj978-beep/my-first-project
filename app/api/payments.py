from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.services.payment import PaymentService

router = APIRouter(prefix="/webhooks", tags=["To'lov"])


@router.post("/payment/click")
async def click_payment_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Click to'lov tizimi webhook (prepare + complete)."""
    form = await request.form()
    data = dict(form)
    service = PaymentService()
    return await service.handle_click_webhook(db, data)


@router.post("/payment/confirm")
async def confirm_payment_manual(
    order_id: int = Form(...),
    secret: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Umumiy to'lov tasdiqlash (demo yoki boshqa provayderlar uchun)."""
    if secret != settings.payment_webhook_secret:
        raise HTTPException(status_code=401, detail="Noto'g'ri kalit")

    service = PaymentService()
    order = await service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")

    await service.complete_order(db, order)
    return {"success": True, "message": "Obuna faollashtirildi"}


pay_page_router = APIRouter(tags=["To'lov"])


@pay_page_router.get("/pay/{order_id}", response_class=HTMLResponse)
async def payment_page(order_id: int, db: AsyncSession = Depends(get_db)):
    """Ota-ona to'lov sahifasi (Click yo'q bo'lsa demo rejim)."""
    service = PaymentService()
    order = await service.get_order(db, order_id)
    if not order:
        return HTMLResponse("<h1>Buyurtma topilmadi</h1>", status_code=404)

    if order.status == "paid":
        return HTMLResponse(
            f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>To'lov</title></head>
            <body style="font-family:sans-serif;text-align:center;padding:40px">
            <h1>✅ To'lov allaqachon qilingan!</h1>
            <p>Obunangiz faol. Telegram botga qayting.</p></body></html>"""
        )

    click_url = service.get_payment_url(order)
    is_demo = not settings.click_service_id

    demo_btn = ""
    if is_demo or settings.payment_demo_mode:
        demo_btn = f"""
        <form method="POST" action="/pay/{order_id}/complete" style="margin-top:20px">
          <button type="submit" style="padding:15px 40px;background:#2563eb;color:white;
            border:none;border-radius:8px;font-size:16px;cursor:pointer">
            💳 To'lov qildim (demo)
          </button>
        </form>
        <p style="color:#666;font-size:13px">Demo rejim — haqiqiy Click ulanganda avtomatik ishlaydi</p>
        """

    click_btn = ""
    if settings.click_service_id:
        click_btn = f"""
        <a href="{click_url}" style="display:inline-block;padding:15px 40px;background:#00A651;
          color:white;text-decoration:none;border-radius:8px;font-size:16px;margin-top:20px">
          💳 Click orqali to'lash
        </a>"""

    return HTMLResponse(f"""<!DOCTYPE html>
    <html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Obuna to'lovi</title></head>
    <body style="font-family:sans-serif;max-width:400px;margin:40px auto;padding:20px;text-align:center">
      <h1>💳 Obuna to'lovi</h1>
      <p style="font-size:24px;font-weight:bold">{order.amount:,} {order.currency}</p>
      <p>Buyurtma #{order.id}</p>
      {click_btn}
      {demo_btn}
    </body></html>""")


@pay_page_router.post("/pay/{order_id}/complete")
async def payment_complete_demo(order_id: int, db: AsyncSession = Depends(get_db)):
    """Demo: to'lov qilindi — obuna avtomatik yoqiladi."""
    if not settings.payment_demo_mode and settings.click_service_id:
        raise HTTPException(status_code=403, detail="Demo rejim o'chirilgan")

    service = PaymentService()
    order = await service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")

    await service.complete_order(db, order, external_id=f"demo-{order_id}")

    return HTMLResponse("""<!DOCTYPE html><html><head><meta charset="utf-8">
    <meta http-equiv="refresh" content="3;url=https://t.me/">
    <title>Muvaffaqiyat</title></head>
    <body style="font-family:sans-serif;text-align:center;padding:40px">
    <h1>✅ To'lov qabul qilindi!</h1>
    <p>Obunangiz avtomatik faollashtirildi.</p>
    <p>Telegram botga qayting — xabarlar keladi!</p>
    </body></html>""")
