import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.config import settings
from app.database import SessionLocal
from app.models.parent import Parent, StudentParent
from app.models.student import Student
from app.services.payment import PaymentService
from app.services.subscription import SubscriptionService
from app.utils.phone import format_phone, normalize_phone, phones_match

log = logging.getLogger(__name__)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "Farzandingiz maktabga kirishi/chiqishini xabar qilaman.\n\n"
        "<b>Buyruqlar:</b>\n"
        "/register &lt;id&gt; &lt;telefon&gt; — Ro'yxatdan o'tish\n"
        "/pay — Obuna to'lovi\n"
        "/status — Obuna holati\n"
        "/mystudents — Farzandlar\n"
        "/help — Yordam",
        parse_mode="HTML",
    )


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "1. Admin sizni qo'shadi va ID beradi\n"
        "2. <code>/register 5 901234567</code> yozing (ID + telefon)\n"
        "3. 3 kun bepul sinov\n"
        "4. Keyin <code>/pay</code> — to'lov, obuna avtomatik yoqiladi",
        parse_mode="HTML",
    )


async def register(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        return await update.message.reply_text(
            "📱 <b>Ro'yxatdan o'tish</b>\n\n"
            "Misol: <code>/register 1 901234567</code>\n"
            "Admin bergan ID va telefon raqamingizni yozing.",
            parse_mode="HTML",
        )
    try:
        pid = int(ctx.args[0])
    except ValueError:
        return await update.message.reply_text("❌ Noto'g'ri ID")
    phone_input = ctx.args[1]
    if not normalize_phone(phone_input):
        return await update.message.reply_text(
            "❌ Noto'g'ri telefon formati.\nMisol: <code>901234567</code> yoki <code>+998901234567</code>",
            parse_mode="HTML",
        )
    chat = update.effective_user.id
    async with SessionLocal() as db:
        p = await db.get(Parent, pid)
        if not p:
            return await update.message.reply_text("❌ ID topilmadi")
        if p.phone:
            if not phones_match(p.phone, phone_input):
                return await update.message.reply_text(
                    "❌ Telefon raqami mos kelmadi.\n"
                    "Admin panelda kiritilgan raqam bilan bir xil bo'lishi kerak."
                )
        else:
            p.phone = format_phone(phone_input)
        ex = await db.execute(select(Parent).where(Parent.telegram_chat_id == chat, Parent.id != pid))
        if ex.scalar_one_or_none():
            return await update.message.reply_text("❌ Bu hisob boshqa ota-onaga bog'langan")
        p.telegram_chat_id = chat
        p.telegram_username = update.effective_user.username
        if not p.bot_registered_at:
            p.bot_registered_at = datetime.now(timezone.utc)
        await db.commit()
        cfg = await SubscriptionService.get_settings(db)
        st = SubscriptionService.status(p, cfg)
        r = await db.execute(select(Student).join(StudentParent).where(StudentParent.parent_id == pid))
        kids = list(r.scalars().all())
    kids_txt = "\n".join(f"• {s.first_name} {s.last_name} ({s.class_name})" for s in kids) or "⚠️ Farzand bog'lanmagan"
    await update.message.reply_text(
        f"✅ <b>Ro'yxatdan o'tdingiz!</b>\n\n👤 {p.full_name}\n{kids_txt}\n\n"
        f"🎁 {cfg.trial_days} kun bepul: {st['label']}",
        parse_mode="HTML",
    )


async def status_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_user.id
    async with SessionLocal() as db:
        r = await db.execute(select(Parent).where(Parent.telegram_chat_id == chat))
        p = r.scalar_one_or_none()
        if not p:
            return await update.message.reply_text("❌ Avval /register qiling")
        cfg = await SubscriptionService.get_settings(db)
        st = SubscriptionService.status(p, cfg)
    await update.message.reply_text(
        f"📊 <b>{p.full_name}</b>\nHolat: <b>{st['label']}</b>\n"
        f"💰 {cfg.subscription_price:,} {cfg.currency} / {cfg.subscription_period_days} kun\n\n/pay — to'lov",
        parse_mode="HTML",
    )


async def pay_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_user.id
    ps = PaymentService()
    async with SessionLocal() as db:
        r = await db.execute(select(Parent).where(Parent.telegram_chat_id == chat))
        p = r.scalar_one_or_none()
        if not p:
            return await update.message.reply_text("❌ Avval /register qiling")
        cfg = await SubscriptionService.get_settings(db)
        st = SubscriptionService.status(p, cfg)
        if st["code"] == "active":
            return await update.message.reply_text(f"✅ Obuna faol: {st['label']}")
        order = await ps.create_order(db, p, cfg)
        url = ps.pay_url(order, cfg)
        msg = ps.pay_message(order, cfg)
    buttons = []
    if url:
        buttons.append([InlineKeyboardButton("💳 Click orqali to'lash", url=url)])
    kb = InlineKeyboardMarkup(buttons) if buttons else None
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=kb)


async def mystudents(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_user.id
    async with SessionLocal() as db:
        r = await db.execute(select(Parent).where(Parent.telegram_chat_id == chat))
        p = r.scalar_one_or_none()
        if not p:
            return await update.message.reply_text("❌ /register qiling")
        r = await db.execute(select(Student).join(StudentParent).where(StudentParent.parent_id == p.id))
        kids = list(r.scalars().all())
    if not kids:
        return await update.message.reply_text("Farzand topilmadi")
    txt = "\n".join(f"• {s.first_name} {s.last_name} — {s.class_name} ({s.card_id})" for s in kids)
    await update.message.reply_text(f"👨‍👩‍👧 <b>Farzandlar:</b>\n\n{txt}", parse_mode="HTML")


def run_bot():
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN kerak")
    log.info("Bot ishga tushmoqda...")
    app = Application.builder().token(settings.telegram_bot_token).build()
    for cmd, fn in [("start", start), ("help", help_cmd), ("register", register),
                    ("status", status_cmd), ("pay", pay_cmd), ("mystudents", mystudents)]:
        app.add_handler(CommandHandler(cmd, fn))
    app.run_polling()
