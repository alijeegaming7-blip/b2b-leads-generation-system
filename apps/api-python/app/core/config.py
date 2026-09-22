from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "Ezitech B2B Sales API"
    APP_VERSION: str = "1.0.0"
    ENV: str = "development"
    PORT: int = 3001
    API_PREFIX: str = "/api"

    # Database — PostgreSQL for production, SQLite for local dev
    # PostgreSQL: postgresql+asyncpg://user:pass@host:5432/db
    # SQLite:     sqlite+aiosqlite:///./ezitech.db
    DATABASE_URL: str = "sqlite+aiosqlite:///./ezitech.db"

    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ENCRYPTION_KEY: str  # 32-byte key for encrypting integration secrets

    # AI — Grok (primary)
    GROK_API_KEY: Optional[str] = None
    GROK_MODEL: str = "grok-beta"

    # AI — OpenAI (fallback)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: Optional[str] = None

    # AI — Local (Ollama / LM Studio)
    LOCAL_AI_BASE_URL: Optional[str] = None
    LOCAL_AI_MODEL: str = "llama3"

    # Email (Gmail)
    GMAIL_USER: Optional[str] = None
    GMAIL_APP_PASSWORD: Optional[str] = None
    GMAIL_DAILY_LIMIT: int = 50
    GMAIL_DELAY_SECONDS: int = 90

    # Redis (for Celery)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Frontend
    NEXT_PUBLIC_APP_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    # Rate limiting
    THROTTLE_REQUESTS_PER_MINUTE: int = 60

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
