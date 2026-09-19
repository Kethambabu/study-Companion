import pytest
from httpx import AsyncClient

from app.modules.admin.service import AdminService, set_user_admin
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import SignupRequest
from app.modules.observability.schemas import AIObservabilityLogCreate
from app.modules.observability.service import ObservabilityService


@pytest.mark.asyncio
async def test_admin_authorization_and_non_admin_denial(async_client: AsyncClient):
    auth_service = AuthService()

    # Create admin user & regular user
    admin_token = await auth_service.signup(
        SignupRequest(email="admin_user_phase9@example.com", password="Password123!", full_name="Admin User")
    )
    admin_id = admin_token.user.id
    set_user_admin(admin_id, True)

    regular_token = await auth_service.signup(
        SignupRequest(email="regular_user_phase9@example.com", password="Password123!", full_name="Regular User")
    )
    regular_id = regular_token.user.id
    set_user_admin(regular_id, False)

    # Regular user attempting admin access -> 403 TenantAccessDenied
    resp_denied = await async_client.get(
        "/api/v1/admin/overview",
        headers={"Authorization": f"Bearer {regular_token.access_token}"},
    )
    assert resp_denied.status_code == 403

    # Admin user accessing admin overview -> 200 OK
    resp_ok = await async_client.get(
        "/api/v1/admin/overview",
        headers={"Authorization": f"Bearer {admin_token.access_token}"},
    )
    assert resp_ok.status_code == 200
    json_data = resp_ok.json()
    assert json_data["system_health_status"] == "healthy"
    assert json_data["total_users"] >= 2


@pytest.mark.asyncio
async def test_analytics_correctness_and_global_aggregation(async_client: AsyncClient):
    auth_service = AuthService()
    token_resp = await auth_service.signup(
        SignupRequest(email="analytics_tester@example.com", password="Password123!", full_name="Analytics Tester")
    )

    resp = await async_client.get(
        "/api/v1/analytics/global",
        headers={"Authorization": f"Bearer {token_resp.access_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_users"] >= 1
    assert data["total_spaces"] >= 1
    assert len(data["activity_timeline"]) == 7


@pytest.mark.asyncio
async def test_ai_observability_telemetry_recording_and_metrics(async_client: AsyncClient):
    auth_service = AuthService()
    token_resp = await auth_service.signup(
        SignupRequest(email="obs_admin@example.com", password="Password123!", full_name="Observability Admin")
    )
    set_user_admin(token_resp.user.id, True)

    obs_service = ObservabilityService()

    # Record telemetry entries
    await obs_service.log_ai_telemetry(
        AIObservabilityLogCreate(
            request_id="req_test_101",
            user_id=token_resp.user.id,
            feature="tutor",
            provider="groq",
            model="llama-3.3-70b-versatile",
            latency_ms=120.5,
            tokens_used=450,
            success=True,
        )
    )

    await obs_service.log_ai_telemetry(
        AIObservabilityLogCreate(
            request_id="req_test_102",
            user_id=token_resp.user.id,
            feature="evaluation",
            provider="gemini",
            model="gemini-1.5-flash",
            latency_ms=210.0,
            tokens_used=320,
            success=False,
            error_category="prompt_injection",
        )
    )

    # Fetch AI usage list via admin endpoint
    resp = await async_client.get(
        "/api/v1/admin/ai-usage",
        headers={"Authorization": f"Bearer {token_resp.access_token}"},
    )
    assert resp.status_code == 200
    logs = resp.json()
    assert len(logs) >= 2

    # Fetch AI evaluation metrics
    resp_eval = await async_client.get(
        "/api/v1/admin/ai-evaluation",
        headers={"Authorization": f"Bearer {token_resp.access_token}"},
    )
    assert resp_eval.status_code == 200
    metrics = resp_eval.json()
    assert metrics["total_requests"] >= 2
    assert metrics["prompt_injection_attempts"] >= 1


@pytest.mark.asyncio
async def test_background_job_status_observability(async_client: AsyncClient):
    auth_service = AuthService()
    token_resp = await auth_service.signup(
        SignupRequest(email="job_admin@example.com", password="Password123!", full_name="Job Admin")
    )
    set_user_admin(token_resp.user.id, True)

    obs_service = ObservabilityService()
    await obs_service.record_job(
        job_type="material_processing",
        status="completed",
        duration_ms=1450.0,
        payload={"material_id": "mat_123", "pages": 12},
    )

    resp = await async_client.get(
        "/api/v1/admin/jobs?status=completed",
        headers={"Authorization": f"Bearer {token_resp.access_token}"},
    )
    assert resp.status_code == 200
    jobs = resp.json()
    assert len(jobs) >= 1
    assert jobs[0]["job_type"] == "material_processing"
    assert jobs[0]["status"] == "completed"
