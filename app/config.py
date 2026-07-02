from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    telegram_bot_token: str = ""
    turnstile_api_key: str = ""
    admin_api_key: str = ""
    database_url: str = "sqlite:///./school.db"
    port: int = 8000
    school_name: str = "Maktab"


settings = Settings()
