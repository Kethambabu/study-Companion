import pytest
from fastapi import APIRouter
from httpx import AsyncClient

from app.core.exceptions import (
    AIProviderError,
    EntityNotFoundError,
    TenantAccessDeniedError,
    UnauthorizedAccessError,
)
from app.main import app

dummy_router = APIRouter(prefix="/test-exceptions")


@dummy_router.get("/not-found")
async def trigger_not_found():
    raise EntityNotFoundError(entity_name="Project", entity_id="proj_123")


@dummy_router.get("/unauthorized")
async def trigger_unauthorized():
    raise UnauthorizedAccessError()


@dummy_router.get("/tenant-denied")
async def trigger_tenant_denied():
    raise TenantAccessDeniedError()


@dummy_router.get("/ai-error")
async def trigger_ai_error():
    raise AIProviderError(provider="groq", message="Rate limit exceeded")


@dummy_router.get("/unhandled")
async def trigger_unhandled():
    raise RuntimeError("Simulated unhandled internal failure")


app.include_router(dummy_router)


@pytest.mark.asyncio
async def test_entity_not_found_handler(async_client: AsyncClient):
    response = await async_client.get("/test-exceptions/not-found")
    assert response.status_code == 404
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "ENTITY_NOT_FOUND"
    assert "Project with id 'proj_123' was not found" in json_data["error"]["message"]


@pytest.mark.asyncio
async def test_unauthorized_handler(async_client: AsyncClient):
    response = await async_client.get("/test-exceptions/unauthorized")
    assert response.status_code == 401
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_tenant_access_denied_handler(async_client: AsyncClient):
    response = await async_client.get("/test-exceptions/tenant-denied")
    assert response.status_code == 403
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "TENANT_ACCESS_DENIED"


@pytest.mark.asyncio
async def test_ai_provider_error_handler(async_client: AsyncClient):
    response = await async_client.get("/test-exceptions/ai-error")
    assert response.status_code == 502
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "AI_PROVIDER_ERROR"


@pytest.mark.asyncio
async def test_unhandled_exception_handler(async_client: AsyncClient):
    try:
        response = await async_client.get("/test-exceptions/unhandled")
        assert response.status_code == 500
        json_data = response.json()
        assert json_data["success"] is False
        assert json_data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    except RuntimeError as e:
        assert "Simulated unhandled internal failure" in str(e)


@pytest.mark.asyncio
async def test_request_id_header_propagation(async_client: AsyncClient):
    custom_id = "req_custom_test_12345"
    response = await async_client.get("/health", headers={"x-request-id": custom_id})
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == custom_id
    json_data = response.json()
    assert json_data["meta"]["request_id"] == custom_id
