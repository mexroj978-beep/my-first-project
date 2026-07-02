from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    migrate_db()


def migrate_db() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    with engine.begin() as connection:
        columns = {row[1] for row in connection.execute(text("PRAGMA table_info(parents)"))}
        if "consent_accepted_at" not in columns:
            connection.execute(text("ALTER TABLE parents ADD COLUMN consent_accepted_at DATETIME"))
        if "trial_expires_at" not in columns:
            connection.execute(text("ALTER TABLE parents ADD COLUMN trial_expires_at DATETIME"))
