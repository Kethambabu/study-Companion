import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    """Verify root /health endpoint returns HTTP 200 OK and expected envelope structure."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "healthy"
    assert "version" in json_data["data"]
    assert "environment" in json_data["data"]
    assert json_data["meta"]["request_id"] is not None


@pytest.mark.asyncio
async def test_api_v1_health_endpoint(async_client: AsyncClient):
    """Verify /api/v1/health endpoint returns HTTP 200 OK."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "healthy"
