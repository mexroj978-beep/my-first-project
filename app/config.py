from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Maktab Xabarnoma"
    database_url: str = "sqlite+aiosqlite:///./xabarnoma.db"
    telegram_bot_token: str = ""
    webhook_secret: str = "change-me-in-production"
    admin_api_key: str = "admin-secret-key"
    timezone: str = "Asia/Tashkent"
    app_base_url: str = "http://localhost:8000"
    payment_demo_mode: bool = True
    payment_webhook_secret: str = "payment-secret"
    click_service_id: str = ""
    click_merchant_id: str = ""
    click_secret_key: str = ""


settings = Settings()
