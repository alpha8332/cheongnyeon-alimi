from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "cheongnyeon-alimi-backend"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/cheongnyeon_alimi"
    TEST_DATABASE_URL: Optional[str] = None
    SQL_ECHO: bool = False

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Admin Access Control (Backend 04)
    ADMIN_PIN_HASH: Optional[str] = None
    ADMIN_SESSION_EXPIRE_MINUTES: int = 60
    ADMIN_MAX_LOGIN_ATTEMPTS: int = 5
    ADMIN_LOCKOUT_SECONDS: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
