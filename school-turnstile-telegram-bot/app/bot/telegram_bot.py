import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.services.attendance import get_or_create_parent, get_student_by_code, link_parent_to_student
from app.services.subscriptions import (
    accept_consent,
    format_subscription_status,
    has_accepted_consent,
    is_access_active,
)

logger = logging.getLogger(__name__)

dp = Dispatcher()
_bot: Bot | None = None


def get_bot() -> Bot:
    global _bot
    if _bot is None:
        if not settings.telegram_bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN o'rnatilmagan")
        _bot = Bot(token=settings.telegram_bot_token)
    return _bot


def get_db_session() -> Session:
    return SessionLocal()


def consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Roziman, davom etish", callback_data="accept_consent")]
        ]
    )


def consent_text() -> str:
    return (
        "📄 <b>Ota-ona rozilik shartnomasi</b>\n\n"
        f"{settings.parent_consent_text}\n\n"
        "✅ Rozilik bildirganingizdan so'ng 3 kun bepul foydalanish boshlanadi.\n"
        "💳 4-kundan boshlab xabar olish uchun obuna talab qilinadi."
    )


async def send_consent_prompt(message: Message) -> None:
    await message.answer(consent_text(), reply_markup=consent_keyboard(), parse_mode="HTML")


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    text = (
        f"👋 Assalomu alaykum!\n\n"
        f"<b>{settings.school_name}</b> davomat tizimiga xush kelibsiz.\n\n"
        f"Farzandingiz maktabga kirgani yoki chiqqani haqida "
        f"xabar olish uchun avval rozilik shartnomasini tasdiqlang.\n\n"
        f"📌 <b>1-qadam:</b> /rozilik\n"
        f"📌 <b>2-qadam:</b> <code>/royxat KOD</code>\n\n"
        f"Rozilikdan keyin {settings.free_trial_days} kun bepul foydalanasiz. "
        f"Keyin obuna talab qilinadi.\n\n"
        f"📌 <b>Ro'yxatdan o'tish:</b>\n"
        f"<code>/royxat KOD</code>\n\n"
        f"Maktabdan berilgan ro'yxatdan o'tish kodini kiriting.\n"
        f"Misol: <code>/royxat ABC12345</code>\n\n"
        f"📋 Boshqa buyruqlar:\n"
        f"/rozilik — shartnomani o'qish va tasdiqlash\n"
        f"/farzandlar — bog'langan farzandlar\n"
        f"/tolov — obuna va to'lov ma'lumotlari\n"
        f"/yordam — yordam"
    )
    await message.answer(text, parse_mode="HTML")
    await send_consent_prompt(message)


@dp.message(Command("rozilik"))
async def cmd_consent(message: Message) -> None:
    db = get_db_session()
    try:
        parent = get_or_create_parent(
            db,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
        )
        if has_accepted_consent(parent):
            await message.answer(
                "✅ Siz rozilik shartnomasini tasdiqlagansiz.\n\n"
                f"{format_subscription_status(db, parent.id)}",
                parse_mode="HTML",
            )
            return
    finally:
        db.close()

    await send_consent_prompt(message)


@dp.callback_query(F.data == "accept_consent")
async def accept_consent_callback(callback: CallbackQuery) -> None:
    db = get_db_session()
    try:
        parent = get_or_create_parent(
            db,
            telegram_id=callback.from_user.id,
            full_name=callback.from_user.full_name,
        )
        was_accepted = has_accepted_consent(parent)
        parent = accept_consent(db, parent)
        await callback.answer("Rozilik qabul qilindi")
        text = (
            "✅ <b>Roziligingiz qabul qilindi.</b>\n\n"
            if not was_accepted
            else "ℹ️ <b>Rozilik oldin tasdiqlangan.</b>\n\n"
        )
        text += (
            f"{settings.free_trial_days} kunlik bepul sinov muddati faol.\n"
            f"Tugash sanasi: {parent.trial_expires_at.strftime('%d.%m.%Y')}\n\n"
            "Endi farzandingiz kodini yuboring:\n"
            "<code>/royxat KOD</code>"
        )
        if callback.message:
            await callback.message.answer(text, parse_mode="HTML")
    finally:
        db.close()


@dp.message(Command("royxat"))
async def cmd_register(message: Message) -> None:
    if not message.text:
        await message.answer("❌ Iltimos, kodni kiriting.\nMisol: <code>/royxat ABC12345</code>", parse_mode="HTML")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "❌ Ro'yxatdan o'tish kodi kiritilmagan.\n\n"
            "Misol: <code>/royxat ABC12345</code>\n\n"
            "Kodni maktab ma'muriyatidan oling.",
            parse_mode="HTML",
        )
        return

    code = parts[1].strip().upper()
    db = get_db_session()
    try:
        parent = get_or_create_parent(
            db,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
        )
        if not has_accepted_consent(parent):
            await message.answer(
                "📄 Ro'yxatdan o'tishdan oldin rozilik shartnomasini tasdiqlang.",
                parse_mode="HTML",
            )
            await send_consent_prompt(message)
            return

        student = get_student_by_code(db, code)
        if student is None:
            await message.answer(
                "❌ Noto'g'ri kod yoki kod mavjud emas.\n"
                "Iltimos, maktab ma'muriyatidan to'g'ri kodni oling."
            )
            return

        linked = link_parent_to_student(db, parent, student)

        if linked:
            subscription_note = (
                "✅ Foydalanish muddatingiz faol, xabarlar yuboriladi."
                if is_access_active(db, parent)
                else "💳 Xabar olish uchun /tolov buyrug'i orqali obunani faollashtiring."
            )
            await message.answer(
                f"✅ <b>Muvaffaqiyatli bog'landi!</b>\n\n"
                f"👤 Farzand: <b>{student.full_name}</b>\n"
                f"🏫 Sinf: <b>{student.class_name}</b>\n\n"
                f"{subscription_note}",
                parse_mode="HTML",
            )
        else:
            await message.answer(
                f"ℹ️ Siz allaqachon <b>{student.full_name}</b> "
                f"({student.class_name}) bilan bog'langansiz.",
                parse_mode="HTML",
            )
    finally:
        db.close()


@dp.message(Command("farzandlar"))
async def cmd_children(message: Message) -> None:
    db = get_db_session()
    try:
        parent = get_or_create_parent(db, telegram_id=message.from_user.id)
        if not has_accepted_consent(parent):
            await message.answer(
                "📄 Avval rozilik shartnomasini tasdiqlang: /rozilik",
                parse_mode="HTML",
            )
            return
        students = [link.student for link in parent.student_links]

        if not students:
            await message.answer(
                "📭 Hozircha hech qanday farzand bog'lanmagan.\n\n"
                "Ro'yxatdan o'tish uchun:\n"
                "<code>/royxat KOD</code>",
                parse_mode="HTML",
            )
            return

        lines = ["👨‍👩‍👧 <b>Sizning farzandlaringiz:</b>\n"]
        for i, student in enumerate(students, 1):
            lines.append(f"{i}. <b>{student.full_name}</b> — {student.class_name}-sinf")
        lines.append(f"\n💳 {format_subscription_status(db, parent.id)}")
        await message.answer("\n".join(lines), parse_mode="HTML")
    finally:
        db.close()


@dp.message(Command("tolov"))
async def cmd_payment(message: Message) -> None:
    db = get_db_session()
    try:
        parent = get_or_create_parent(
            db,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
        )
        status = format_subscription_status(db, parent.id)
        students = [link.student for link in parent.student_links]
        children_text = (
            "\n".join(f"• {student.full_name} ({student.class_name})" for student in students)
            if students
            else "Hali farzand bog'lanmagan. Avval /royxat KOD buyrug'idan foydalaning."
        )

        await message.answer(
            "💳 <b>Obuna va to'lov</b>\n\n"
            f"{status}\n\n"
            f"👨‍👩‍👧 <b>Bog'langan farzandlar:</b>\n{children_text}\n\n"
            f"💰 30 kunlik obuna: <b>{settings.monthly_subscription_amount:,} so'm</b>\n\n"
            f"📌 <b>To'lov yo'riqnomasi:</b>\n{settings.payment_instructions}\n\n"
            "To'lov tasdiqlangach, admin obunangizni faollashtiradi.",
            parse_mode="HTML",
        )
    finally:
        db.close()


@dp.message(Command("yordam"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "📖 <b>Yordam</b>\n\n"
        "<b>/rozilik</b> — shartnomani o'qish va tasdiqlash\n"
        "<b>/royxat KOD</b> — farzandni bog'lash\n"
        "<b>/farzandlar</b> — bog'langan farzandlar ro'yxati\n"
        "<b>/tolov</b> — obuna holati va to'lov yo'riqnomasi\n"
        "<b>/yordam</b> — ushbu xabar\n\n"
        "❓ Savollar bo'lsa, maktab ma'muriyatiga murojaat qiling.",
        parse_mode="HTML",
    )


@dp.message(F.text)
async def unknown_message(message: Message) -> None:
    await message.answer(
        "🤔 Tushunmadim. Yordam uchun /yordam buyrug'ini yuboring."
    )


async def start_bot() -> None:
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN o'rnatilmagan — bot ishga tushmaydi")
        return
    logger.info("Telegram bot ishga tushmoqda...")
    bot = get_bot()
    await dp.start_polling(bot)


def run_bot_in_background() -> asyncio.Task[None] | None:
    if not settings.telegram_bot_token:
        return None
    return asyncio.create_task(start_bot())
