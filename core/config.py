"""
Centralised configuration via Pydantic Settings.
All values are read from environment variables or a .env file.
Never hard-code secrets — add them to .env and reference them here.
"""
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Application ─────────────────────────────────────────
    APP_ENV: str = "development"        # development | production
    DEBUG: bool = True
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8501"]

    # ── LLM ─────────────────────────────────────────────────
    GROQ_API_KEY: str
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 2048
    LLM_MAX_RETRIES: int = 3

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://mathbot:mathbot@localhost:5432/mathbot"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ── Redis ────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 3600           # 1 hour default

    # ── Security ─────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Rate Limiting ────────────────────────────────────────
    RATE_LIMIT_SOLVE_PER_MINUTE: int = 20
    RATE_LIMIT_OCR_PER_MINUTE: int = 5

    # ── OCR ──────────────────────────────────────────────────
    OCR_CONFIDENCE_THRESHOLD: float = 0.85
    MAX_IMAGE_SIZE_MB: int = 10

    # ── Agent ────────────────────────────────────────────────
    AGENT_MAX_ITERATIONS: int = 8
    AGENT_TIMEOUT_SECONDS: int = 60
    VERIFICATION_CONFIDENCE_THRESHOLD: float = 0.80
    SANDBOX_TIMEOUT_SECONDS: float = 5.0

    # ── Celery ───────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Single global instance imported everywhere
settings = Settings()
