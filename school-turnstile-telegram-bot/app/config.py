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
    subscription_period_days: int = 30
    free_trial_days: int = 3
    payment_instructions: str = (
        "To'lov uchun maktab ma'muriyatiga murojaat qiling. "
        "To'lov tasdiqlangach, obunangiz 30 kunga faollashtiriladi."
    )
    parent_consent_text: str = (
        "Men farzandimning maktabga kirish va chiqish vaqtlari tirniket tizimi orqali "
        "qayd etilishi hamda ushbu ma'lumotlar Telegram bot orqali menga xabar sifatida "
        "yuborilishiga rozilik bildiraman. Botdan foydalanish uchun dastlab 3 kun bepul "
        "sinov muddati beriladi, 4-kundan boshlab pullik obuna talab qilinishini tushunaman."
    )


settings = Settings()
