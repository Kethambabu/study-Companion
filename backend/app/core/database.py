from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("database")


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


import asyncio
import os
import re

db_url = settings.DATABASE_URL
if os.getenv("TESTING") == "true" or getattr(settings, "ENVIRONMENT", "") == "testing":
    db_url = "sqlite+aiosqlite:///file:memdb?mode=memory&cache=shared"
elif (
    "[YOUR" in db_url
    or "YOUR_SUPABASE" in db_url
):
    logger.warning("Placeholder detected in DATABASE_URL. Falling back to SQLite shared memory engine.")
    db_url = "sqlite+aiosqlite:///file:memdb?mode=memory&cache=shared"
elif db_url.startswith("postgresql://") or db_url.startswith("postgres://"):
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    db_url = re.sub(r"[?&]pgbouncer=true", "", db_url)

connect_args = {}
if "sqlite" in db_url:
    connect_args["check_same_thread"] = False
elif "postgresql" in db_url:
    connect_args["timeout"] = 15
    connect_args["command_timeout"] = 15

engine_kwargs = {
    "echo": settings.DB_ECHO,
    "future": True,
    "connect_args": connect_args,
}

if "postgresql" in db_url:
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": 20,
        "max_overflow": 10,
        "pool_recycle": 1800,
        "pool_timeout": 30,
    })

engine: AsyncEngine = create_async_engine(
    db_url,
    **engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession | None, None]:
    """Dependency for providing asynchronous database sessions with graceful fallback."""
    try:
        session = AsyncSessionLocal()
    except Exception as e:
        logger.warning(f"Database connection unavailable ({e}). Operating in in-memory mode.")
        yield None
        return

    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
