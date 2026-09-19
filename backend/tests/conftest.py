import os
os.environ["TESTING"] = "true"

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture(autouse=True)
async def init_db():
    from app.core.config import settings
    settings.DATABASE_URL = "sqlite+aiosqlite:///file:memdb?mode=memory&cache=shared"
    from app.core.database import Base, engine
    import app.modules.auth.models  # noqa: F401
    import app.modules.projects.models  # noqa: F401
    import app.modules.materials.models  # noqa: F401
    import app.modules.knowledge.models  # noqa: F401
    import app.modules.tutor.models  # noqa: F401
    import app.modules.assessment.models  # noqa: F401
    import app.modules.mastery.models  # noqa: F401
    import app.modules.recommendations.models  # noqa: F401
    import app.modules.events.models  # noqa: F401
    import app.modules.observability.models  # noqa: F401
    import app.modules.jobs.models  # noqa: F401

    # Clear all in-memory fallback repositories for clean test isolation
    import app.modules.auth.service as auth_svc
    import app.modules.projects.service as proj_svc
    import app.modules.materials.service as mat_svc
    import app.modules.knowledge.service as know_svc
    import app.modules.tutor.service as tut_svc
    import app.modules.assessment.service as ass_svc
    import app.modules.mastery.service as mast_svc
    import app.modules.recommendations.service as rec_svc

    auth_svc._IN_MEMORY_USERS.clear()
    auth_svc._IN_MEMORY_PROFILES.clear()
    auth_svc._IN_MEMORY_SPACES.clear()
    auth_svc._IN_MEMORY_MEMBERS.clear()
    proj_svc._IN_MEMORY_PROJECTS.clear()
    mat_svc._IN_MEMORY_MATERIALS.clear()
    mat_svc._IN_MEMORY_JOBS.clear()
    mat_svc._IN_MEMORY_PAGES.clear()
    know_svc._IN_MEMORY_CHUNKS.clear()
    know_svc._IN_MEMORY_CONCEPTS.clear()
    tut_svc._IN_MEMORY_CONVERSATIONS.clear()
    tut_svc._IN_MEMORY_MESSAGES.clear()
    tut_svc._IN_MEMORY_OBSERVABILITY_LOGS.clear()
    ass_svc._IN_MEMORY_QUIZZES.clear()
    ass_svc._IN_MEMORY_QUESTIONS.clear()
    ass_svc._IN_MEMORY_ATTEMPTS.clear()
    ass_svc._IN_MEMORY_Q_ATTEMPTS.clear()
    ass_svc._IN_MEMORY_RESULTS.clear()
    mast_svc._IN_MEMORY_MASTERY.clear()
    mast_svc._IN_MEMORY_MASTERY_EVENTS.clear()
    mast_svc._IN_MEMORY_PROCESSED_EVENT_IDS.clear()
    mast_svc._IN_MEMORY_GROWTH_SNAPSHOTS.clear()
    rec_svc._IN_MEMORY_RECOMMENDATIONS.clear()
    rec_svc._IN_MEMORY_REC_KEYS.clear()

    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.drop_all)
        except Exception:
            pass
        try:
            await conn.run_sync(Base.metadata.create_all)
        except Exception:
            pass


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provides an HTTPX AsyncClient for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

