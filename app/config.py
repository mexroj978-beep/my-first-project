import re

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

TOKEN_PLACEHOLDER = "your_bot_token_from_botfather"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Maktab Turniket Bot"
    database_url: str = "sqlite+aiosqlite:///./school_attendance.db"
    telegram_bot_token: str = ""

    @field_validator("telegram_bot_token")
    @classmethod
    def _clean_token(cls, v: str) -> str:
        # Nusxalashda tushib qolgan bo'shliq/qo'shtirnoqlarni tozalash
        v = re.sub(r"\s+", "", v).strip("\"'")
        if v == TOKEN_PLACEHOLDER:
            return ""
        return v
    webhook_secret: str = "change-me-in-production"
    admin_api_key: str = "admin-secret-key"
    timezone: str = "Asia/Tashkent"


settings = Settings()
