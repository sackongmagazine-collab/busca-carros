from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Core
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/buscacarros"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 dias

    # AI
    anthropic_api_key: str = ""

    # Limites por plano
    free_searches_per_day: int = 3
    hunter_max_alerts: int = 5
    hunter_pro_max_alerts: int = 20
    dealer_max_listings: int = 500

    # Preços (BRL)
    price_hunter: float = 29.90
    price_hunter_pro: float = 59.90
    price_dealer: float = 149.90

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_hunter: str = ""       # price_xxx do Stripe
    stripe_price_hunter_pro: str = ""
    stripe_price_dealer: str = ""

    # Email — Resend
    resend_api_key: str = ""
    email_from: str = "alertas@buscacarros.com.br"

    # WhatsApp — Evolution API (self-hosted ou cloud)
    evolution_api_url: str = ""
    evolution_api_key: str = ""
    evolution_instance: str = "buscacarros"

    # Telegram
    telegram_bot_token: str = ""

    # FIPE
    fipe_api_base: str = "https://parallelum.com.br/fipe/api/v2"

    # MercadoLivre
    ml_api_base: str = "https://api.mercadolibre.com"

    # App
    app_url: str = "http://localhost:5173"
    admin_secret: str = "admin-secret-change-me"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
