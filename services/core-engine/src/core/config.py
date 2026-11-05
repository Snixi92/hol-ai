"""
Configuration globale du Core Engine HoL AI via Pydantic Settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_ENV: str = "development"
    APP_NAME: str = "HoL AI Core Engine"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Redis / Message Broker
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    USE_FAKEREDIS: bool = True  # Permet une exécution autonome si aucun Redis local n'est détecté

    # PostgreSQL / pgvector
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "hol_ai_db"
    POSTGRES_USER: str = "hol_ai_admin"
    POSTGRES_PASSWORD: str = "change_this_in_production"

    # IA & LLM
    GEMINI_API_KEY: Optional[str] = None
    DEFAULT_MODEL: str = "gemini-2.5-flash"

    # Budgets et Timeouts
    DEFAULT_TOKEN_BUDGET: int = 4096
    DEFAULT_TIMEOUT_MS: int = 15000
    MAX_RETRIES: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
