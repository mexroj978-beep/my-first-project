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
    # Turniket/Face ID webhook — vergul bilan IP lar (bo'sh = hamma ruxsat, mahalliy test uchun)
    turnstile_ip_whitelist: str = ""
    # nginx/Cloudflare orqasida haqiqiy IP ni olish
    trust_proxy_headers: bool = False

    @property
    def turnstile_allowed_ips(self) -> frozenset[str]:
        if not self.turnstile_ip_whitelist.strip():
            return frozenset()
        return frozenset(ip.strip() for ip in self.turnstile_ip_whitelist.split(",") if ip.strip())


settings = Settings()
