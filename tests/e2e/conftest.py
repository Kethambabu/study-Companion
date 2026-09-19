import os
import sys
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from app.main import app


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provides an HTTPX AsyncClient for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
