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
    connect_args["timeout"] = 15.0
    connect_args["command_timeout"] = 15.0
    # Supabase transaction pooler (pgbouncer) doesn't support prepared statements
    connect_args["statement_cache_size"] = 0

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
        "pool_timeout": 15.0,
    })

engine: AsyncEngine = create_async_engine(
    db_url,
    **engine_kwargs,
)

class SafeAsyncSession(AsyncSession):
    """AsyncSession subclass that expunges all ORM instances before every rollback.

    SQLAlchemy marks all tracked instances as 'expired' after rollback. On an async
    (asyncpg) engine, subsequent attribute access on expired instances triggers a
    synchronous lazy-load → MissingGreenlet crash. Expunging them first detaches
    instances so they retain their in-memory attribute values without needing a DB
    round-trip.
    """

    async def rollback(self) -> None:
        try:
            self.expunge_all()
        except Exception:
            pass
        await super().rollback()


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=SafeAsyncSession,   # ← use safe subclass instead of raw AsyncSession
    expire_on_commit=False,
    # NOTE: expire_on_rollback is NOT a valid kwarg for async_sessionmaker in SQLAlchemy 2.0.x
    # It would silently break session creation. Use expire_on_commit=False instead.
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession | None, None]:
    """Dependency for providing asynchronous database sessions with graceful fallback.

    On rollback, all ORM instances are expunged from the session identity map so that
    accessing their attributes after an exception never triggers a lazy-load (which
    would raise MissingGreenlet on an async engine).
    """
    try:
        session = AsyncSessionLocal()
    except Exception as e:
        logger.warning(f"Database connection unavailable ({e}). Operating in in-memory mode.")
        yield None
        return

    try:
        yield session
    except Exception:
        try:
            session.expunge_all()   # detach all instances BEFORE rollback so they don't get expired
            await session.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            await session.close()
        except Exception:
            pass
