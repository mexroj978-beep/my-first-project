import re

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Maktab Turniket Bot"
    database_url: str = "sqlite+aiosqlite:///./school_attendance.db"
    telegram_bot_token: str = ""
    webhook_secret: str = "change-me-in-production"
    admin_api_key: str = "admin-secret-key"
    timezone: str = "Asia/Tashkent"

    @field_validator("telegram_bot_token", mode="before")
    @classmethod
    def normalize_telegram_bot_token(cls, value: str | None) -> str:
        if value is None:
            return ""
        return re.sub(r"\s+", "", str(value))


settings = Settings()
