import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    CELERY_TASK_ALWAYS_EAGER: bool = os.getenv("CELERY_TASK_ALWAYS_EAGER", "False").lower() in ("true", "1", "yes")

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    TIMEZONE: str = "UTC"


worker_settings = WorkerSettings()
