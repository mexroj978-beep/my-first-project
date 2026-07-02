import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.services.attendance import get_or_create_parent, get_student_by_code, link_parent_to_student

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


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    text = (
        f"👋 Assalomu alaykum!\n\n"
        f"<b>{settings.school_name}</b> davomat tizimiga xush kelibsiz.\n\n"
        f"Farzandingiz maktabga kirgani yoki chiqqani haqida "
        f"darhol xabar olish uchun ro'yxatdan o'ting.\n\n"
        f"📌 <b>Ro'yxatdan o'tish:</b>\n"
        f"<code>/royxat KOD</code>\n\n"
        f"Maktabdan berilgan ro'yxatdan o'tish kodini kiriting.\n"
        f"Misol: <code>/royxat ABC12345</code>\n\n"
        f"📋 Boshqa buyruqlar:\n"
        f"/farzandlar — bog'langan farzandlar\n"
        f"/yordam — yordam"
    )
    await message.answer(text, parse_mode="HTML")


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
        student = get_student_by_code(db, code)
        if student is None:
            await message.answer(
                "❌ Noto'g'ri kod yoki kod mavjud emas.\n"
                "Iltimos, maktab ma'muriyatidan to'g'ri kodni oling."
            )
            return

        parent = get_or_create_parent(
            db,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
        )
        linked = link_parent_to_student(db, parent, student)

        if linked:
            await message.answer(
                f"✅ <b>Muvaffaqiyatli bog'landi!</b>\n\n"
                f"👤 Farzand: <b>{student.full_name}</b>\n"
                f"🏫 Sinf: <b>{student.class_name}</b>\n\n"
                f"Endi farzandingiz maktabga kirgani yoki chiqqani "
                f"haqida xabar olasiz.",
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
        await message.answer("\n".join(lines), parse_mode="HTML")
    finally:
        db.close()


@dp.message(Command("yordam"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "📖 <b>Yordam</b>\n\n"
        "<b>/royxat KOD</b> — farzandni bog'lash\n"
        "<b>/farzandlar</b> — bog'langan farzandlar ro'yxati\n"
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
