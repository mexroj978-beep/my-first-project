from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def _migrate_columns(conn) -> None:
    """Mavjud SQLite bazaga yangi ustunlar qo'shish."""
    from sqlalchemy import inspect, text

    def _run(sync_conn):
        insp = inspect(sync_conn)
        if "settings" not in insp.get_table_names():
            return
        cols = {c["name"] for c in insp.get_columns("settings")}
        for name, ddl in (
            ("payment_card_number", "ALTER TABLE settings ADD COLUMN payment_card_number VARCHAR(30)"),
            ("payment_card_holder", "ALTER TABLE settings ADD COLUMN payment_card_holder VARCHAR(100)"),
            ("payment_click_link", "ALTER TABLE settings ADD COLUMN payment_click_link TEXT"),
        ):
            if name not in cols:
                sync_conn.execute(text(ddl))

    await conn.run_sync(_run)


async def init_db() -> None:
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_columns(conn)
