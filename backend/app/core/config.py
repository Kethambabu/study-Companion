
import json
from typing import Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Project metadata
    PROJECT_NAME: str = "AI Study Companion API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Backend server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # CORS
    CORS_ORIGINS: list[str] = [
        "https://study-companion-2.onrender.com",
        "https://study-companion-backend.onrender.com",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped.startswith("[") and v_stripped.endswith("]"):
                try:
                    parsed = json.loads(v_stripped)
                    if isinstance(parsed, list):
                        return [str(item) for item in parsed]
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return [str(item) for item in v]
        return [
            "https://study-companion-2.onrender.com",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]



    # Supabase / Auth
    SUPABASE_URL: str | None = None
    VITE_SUPABASE_URL: str | None = None
    VITE_SUPABASE_PUBLISHABLE_KEY: str | None = None
    SUPABASE_SECRET_KEY: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    JWT_SECRET: str = "dev-secret-change-in-production-32bytes"
    JWT_ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    DB_ECHO: bool = False

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_ALWAYS_EAGER: bool = False

    # AI Provider abstractions defaults (Groq + Gemini multi-provider architecture)
    DEFAULT_AI_PROVIDER: str = "groq"
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "groq/compound"

    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "models/gemini-flash-latest"

    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "sentence-transformers/all-mpnet-base-v2"
    VECTOR_STORE_PROVIDER: str = "pgvector"

    # Frontend
    VITE_API_BASE_URL: str = "http://localhost:8000/api/v1"
    VITE_APP_ENV: str = "development"

    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in ("production", "prod")


settings = Settings()

