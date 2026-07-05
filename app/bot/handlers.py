import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.config import settings
from app.database import async_session
from app.models.parent import Parent, StudentParent
from app.models.student import Student
from app.services.subscription import SubscriptionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    await update.message.reply_text(
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "Bu bot farzandingiz maktabga kirishi va chiqishini xabar qiladi.\n\n"
        "<b>Ro'yxatdan o'tish:</b>\n"
        "Maktab admini sizga berilgan ID raqam bilan:\n"
        "<code>/register 123</code>\n\n"
        "<b>Buyruqlar:</b>\n"
        "/register &lt;id&gt; - Telegram hisobingizni bog'lash\n"
        "/status - Obuna holati\n"
        "/subscribe - Obuna narxi va to'lov\n"
        "/mystudents - Farzandlar ro'yxati\n"
        "/help - Yordam",
        parse_mode="HTML",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    await update.message.reply_text(
        "ℹ️ <b>Yordam</b>\n\n"
        "1. Maktab admini sizni tizimga qo'shadi\n"
        "2. Sizga parent ID beriladi (masalan: 5)\n"
        "3. Botda yozing: <code>/register 5</code>\n"
        "4. <b>3 kun bepul</b> sinov davri boshlanadi\n"
        "5. Keyin obuna bo'ling: <code>/subscribe</code>\n\n"
        "Savollar bo'lsa maktab adminiga murojaat qiling.",
        parse_mode="HTML",
    )


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Parent ID kiriting.\n\nMisol: <code>/register 5</code>",
            parse_mode="HTML",
        )
        return

    try:
        parent_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri ID formati.")
        return

    chat_id = update.effective_user.id
    username = update.effective_user.username

    async with async_session() as session:
        parent = await session.get(Parent, parent_id)
        if not parent:
            await update.message.reply_text("❌ Bunday parent ID topilmadi. Admin bilan bog'laning.")
            return

        existing = await session.execute(
            select(Parent).where(Parent.telegram_chat_id == chat_id, Parent.id != parent_id)
        )
        if existing.scalar_one_or_none():
            await update.message.reply_text("❌ Bu Telegram hisob boshqa ota-onaga bog'langan.")
            return

        parent.telegram_chat_id = chat_id
        parent.telegram_username = username
        if not parent.bot_registered_at:
            parent.bot_registered_at = datetime.now(timezone.utc)
        await session.commit()

        app_settings = await SubscriptionService.get_settings(session)
        sub_status = SubscriptionService.get_status(parent, app_settings)

        result = await session.execute(
            select(Student)
            .join(StudentParent, StudentParent.student_id == Student.id)
            .where(StudentParent.parent_id == parent_id)
            .options(selectinload(Student.school))
        )
        students = list(result.scalars().all())

    if students:
        lines = "\n".join(
            f"• {s.first_name} {s.last_name} ({s.class_name}-sinf)" for s in students
        )
        await update.message.reply_text(
            f"✅ <b>Muvaffaqiyatli ro'yxatdan o'tdingiz!</b>\n\n"
            f"👤 {parent.full_name}\n\n"
            f"<b>Farzandlar:</b>\n{lines}\n\n"
            f"🎁 <b>{app_settings.trial_days} kun bepul</b> sinov boshlandi!\n"
            f"📊 Holat: {sub_status['label']}\n\n"
            f"Sinov tugagach: /subscribe",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            f"✅ Ro'yxatdan o'tdingiz: <b>{parent.full_name}</b>\n\n"
            f"⚠️ Hali farzand bog'lanmagan. Admin bilan bog'laning.\n\n"
            f"🎁 <b>{app_settings.trial_days} kun bepul</b> sinov boshlandi!",
            parse_mode="HTML",
        )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return

    chat_id = update.effective_user.id
    async with async_session() as session:
        result = await session.execute(select(Parent).where(Parent.telegram_chat_id == chat_id))
        parent = result.scalar_one_or_none()
        if not parent:
            await update.message.reply_text("❌ Avval <code>/register ID</code> qiling.", parse_mode="HTML")
            return

        app_settings = await SubscriptionService.get_settings(session)
        sub = SubscriptionService.get_status(parent, app_settings)

    await update.message.reply_text(
        f"📊 <b>Obuna holati</b>\n\n"
        f"👤 {parent.full_name}\n"
        f"📌 Holat: <b>{sub['label']}</b>\n"
        f"💰 Obuna narxi: <b>{app_settings.subscription_price:,} {app_settings.currency}</b> / "
        f"{app_settings.subscription_period_days} kun\n\n"
        f"Obuna bo'lish: /subscribe",
        parse_mode="HTML",
    )


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return

    chat_id = update.effective_user.id
    async with async_session() as session:
        result = await session.execute(select(Parent).where(Parent.telegram_chat_id == chat_id))
        parent = result.scalar_one_or_none()
        app_settings = await SubscriptionService.get_settings(session)

    if not parent:
        await update.message.reply_text("❌ Avval <code>/register ID</code> qiling.", parse_mode="HTML")
        return

    sub = SubscriptionService.get_status(parent, app_settings)
    payment = app_settings.payment_info or "Maktab adminiga murojaat qiling."

    await update.message.reply_text(
        f"💳 <b>Obuna ma'lumotlari</b>\n\n"
        f"💰 Narx: <b>{app_settings.subscription_price:,} {app_settings.currency}</b>\n"
        f"📅 Davr: {app_settings.subscription_period_days} kun\n"
        f"🎁 Bepul sinov: {app_settings.trial_days} kun\n\n"
        f"📌 Sizning holat: <b>{sub['label']}</b>\n\n"
        f"<b>To'lov uchun:</b>\n{payment}\n\n"
        f"To'lovdan keyin admin obunani faollashtiradi.",
        parse_mode="HTML",
    )


async def mystudents_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return

    chat_id = update.effective_user.id

    async with async_session() as session:
        result = await session.execute(
            select(Parent).where(Parent.telegram_chat_id == chat_id, Parent.is_active.is_(True))
        )
        parent = result.scalar_one_or_none()
        if not parent:
            await update.message.reply_text(
                "❌ Siz ro'yxatdan o'tmagansiz.\n\n<code>/register &lt;id&gt;</code> buyrug'ini yuboring.",
                parse_mode="HTML",
            )
            return

        result = await session.execute(
            select(Student)
            .join(StudentParent, StudentParent.student_id == Student.id)
            .where(StudentParent.parent_id == parent.id)
        )
        students = list(result.scalars().all())

    if not students:
        await update.message.reply_text("Farzandlar topilmadi.")
        return

    lines = "\n".join(
        f"• {s.first_name} {s.last_name} — {s.class_name}-sinf (karta: {s.card_id})"
        for s in students
    )
    await update.message.reply_text(
        f"👨‍👩‍👧 <b>Sizning farzandlaringiz:</b>\n\n{lines}",
        parse_mode="HTML",
    )


def build_bot_application() -> Application:
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN sozlanmagan")

    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("register", register_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("subscribe", subscribe_command))
    app.add_handler(CommandHandler("mystudents", mystudents_command))
    return app


def run_bot() -> None:
    logger.info("Telegram bot ishga tushmoqda...")
    app = build_bot_application()
    app.run_polling(allowed_updates=Update.ALL_TYPES)
