from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    telegram_bot_token: str = ""
    turnstile_api_key: str = ""
    admin_api_key: str = ""
    database_url: str = "sqlite:///./school.db"
    port: int = 8000
    school_name: str = "Maktab"
    monthly_subscription_amount: int = 30000
    payment_instructions: str = (
        "To'lov uchun maktab ma'muriyatiga murojaat qiling. "
        "To'lov tasdiqlangach, obunangiz 1 oyga faollashtiriladi."
    )


settings = Settings()
