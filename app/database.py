from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def init_db() -> None:
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_columns(conn)


async def _migrate_columns(conn) -> None:
    """Mavjud SQLite bazaga yangi ustunlar qo'shish."""
    migrations = [
        "ALTER TABLE parents ADD COLUMN bot_registered_at DATETIME",
        "ALTER TABLE parents ADD COLUMN subscription_until DATETIME",
    ]
    for sql in migrations:
        try:
            await conn.exec_driver_sql(sql)
        except Exception:
            pass
