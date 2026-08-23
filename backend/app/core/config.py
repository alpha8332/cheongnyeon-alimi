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

    # Central collection queue
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: Optional[str] = None
    COLLECTION_QUEUE_NAME: str = "collection"
    COLLECTION_TASK_SOFT_TIME_LIMIT_SECONDS: int = 900
    COLLECTION_TASK_TIME_LIMIT_SECONDS: int = 960
    COLLECTION_TASK_MAX_RETRIES: int = 5
    COLLECTION_TASK_RETRY_BACKOFF_MAX_SECONDS: int = 300
    COLLECTION_TASK_RATE_LIMIT: str = "6/m"
    COLLECTION_SCHEDULE_ENABLED: bool = False
    COLLECTION_SCHEDULE_SOURCE_ID: str = "youthcenter-api"
    COLLECTION_SCHEDULE_REQUESTED_COUNT: int = 100
    COLLECTION_SCHEDULE_COMPLETE_SNAPSHOT: bool = False
    COLLECTION_SNAPSHOT_REQUEST_BUDGET: int = 12
    COLLECTION_SCHEDULE_CRON_HOUR: int = 3
    COLLECTION_SCHEDULE_CRON_MINUTE: int = 0

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Admin Access Control (Backend 04)
    ADMIN_PIN_HASH: Optional[str] = None
    ADMIN_TOKEN_SECRET: Optional[str] = None
    ADMIN_SESSION_EXPIRE_MINUTES: int = 60
    ADMIN_MAX_LOGIN_ATTEMPTS: int = 5
    ADMIN_LOCKOUT_SECONDS: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
