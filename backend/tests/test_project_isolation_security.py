import uuid
import pytest
from httpx import AsyncClient

from app.modules.auth.service import AuthService
from app.modules.auth.schemas import SignupRequest


@pytest.mark.asyncio
async def test_user_a_cannot_access_user_b_spaces_and_projects(async_client: AsyncClient):
    auth_service = AuthService()

    user_a = await auth_service.signup(
        SignupRequest(email="user_a_sec@example.com", password="Password123!", full_name="User A")
    )
    headers_a = {"Authorization": f"Bearer {user_a.access_token}"}

    user_b = await auth_service.signup(
        SignupRequest(email="user_b_sec@example.com", password="Password123!", full_name="User B")
    )
    headers_b = {"Authorization": f"Bearer {user_b.access_token}"}

    sp_b_res = await async_client.post(
        "/api/v1/spaces",
        json={"name": "User B Private Space", "slug": "user-b-private-space"},
        headers=headers_b,
    )
    assert sp_b_res.status_code == 201
    space_b_id = sp_b_res.json()["data"]["id"]

    proj_b_res = await async_client.post(
        "/api/v1/projects",
        json={"space_id": space_b_id, "name": "User B Secret Project"},
        headers=headers_b,
    )
    assert proj_b_res.status_code == 201
    proj_b_id = proj_b_res.json()["data"]["id"]

    # User A attempts to access User B project -> 403 Forbidden
    get_proj_res = await async_client.get(f"/api/v1/projects/{proj_b_id}", headers=headers_a)
    assert get_proj_res.status_code == 403

    # User A attempts to update User B project -> 403 Forbidden
    update_proj_res = await async_client.patch(
        f"/api/v1/projects/{proj_b_id}",
        json={"name": "Hacked Title"},
        headers=headers_a,
    )
    assert update_proj_res.status_code == 403


@pytest.mark.asyncio
async def test_user_a_cannot_access_user_b_materials_and_tutor(async_client: AsyncClient):
    auth_service = AuthService()
    user_a = await auth_service.signup(
        SignupRequest(email="user_a_mat@example.com", password="Password123!", full_name="User A")
    )
    headers_a = {"Authorization": f"Bearer {user_a.access_token}"}

    user_b = await auth_service.signup(
        SignupRequest(email="user_b_mat@example.com", password="Password123!", full_name="User B")
    )
    headers_b = {"Authorization": f"Bearer {user_b.access_token}"}

    sp_b = await async_client.post(
        "/api/v1/spaces", json={"name": "Space B", "slug": "space-b-mat"}, headers=headers_b
    )
    sp_b_id = sp_b.json()["data"]["id"]
    pj_b = await async_client.post(
        "/api/v1/projects", json={"space_id": sp_b_id, "name": "Project B Mat"}, headers=headers_b
    )
    pj_b_id = pj_b.json()["data"]["id"]

    # User A attempts to list User B materials -> 403 Forbidden
    mat_res = await async_client.get(f"/api/v1/projects/{pj_b_id}/materials", headers=headers_a)
    assert mat_res.status_code == 403

    # User A attempts to access User B AI Tutor conversations -> 403 Forbidden
    tutor_res = await async_client.get(f"/api/v1/projects/{pj_b_id}/tutor/conversations", headers=headers_a)
    assert tutor_res.status_code == 403


@pytest.mark.asyncio
async def test_user_a_cannot_access_user_b_quizzes_and_mastery(async_client: AsyncClient):
    auth_service = AuthService()
    user_a = await auth_service.signup(
        SignupRequest(email="user_a_quiz@example.com", password="Password123!", full_name="User A")
    )
    headers_a = {"Authorization": f"Bearer {user_a.access_token}"}

    user_b = await auth_service.signup(
        SignupRequest(email="user_b_quiz@example.com", password="Password123!", full_name="User B")
    )
    headers_b = {"Authorization": f"Bearer {user_b.access_token}"}

    sp_b = await async_client.post(
        "/api/v1/spaces", json={"name": "Space B Quiz", "slug": "space-b-quiz"}, headers=headers_b
    )
    sp_b_id = sp_b.json()["data"]["id"]
    pj_b = await async_client.post(
        "/api/v1/projects", json={"space_id": sp_b_id, "name": "Project B Quiz"}, headers=headers_b
    )
    pj_b_id = pj_b.json()["data"]["id"]

    # User A attempts to list/create quizzes in User B project -> 403 Forbidden
    quiz_res = await async_client.get(f"/api/v1/projects/{pj_b_id}/quizzes", headers=headers_a)
    assert quiz_res.status_code == 403

    # User A attempts to fetch User B mastery summary -> 403 Forbidden
    mastery_res = await async_client.get(f"/api/v1/projects/{pj_b_id}/growth/summary", headers=headers_a)
    assert mastery_res.status_code == 403


@pytest.mark.asyncio
async def test_user_a_cannot_access_user_b_recommendations_and_analytics(async_client: AsyncClient):
    auth_service = AuthService()
    user_a = await auth_service.signup(
        SignupRequest(email="user_a_rec@example.com", password="Password123!", full_name="User A")
    )
    headers_a = {"Authorization": f"Bearer {user_a.access_token}"}

    user_b = await auth_service.signup(
        SignupRequest(email="user_b_rec@example.com", password="Password123!", full_name="User B")
    )
    headers_b = {"Authorization": f"Bearer {user_b.access_token}"}

    sp_b = await async_client.post(
        "/api/v1/spaces", json={"name": "Space B Rec", "slug": "space-b-rec"}, headers=headers_b
    )
    sp_b_id = sp_b.json()["data"]["id"]
    pj_b = await async_client.post(
        "/api/v1/projects", json={"space_id": sp_b_id, "name": "Project B Rec"}, headers=headers_b
    )
    pj_b_id = pj_b.json()["data"]["id"]

    # User A attempts to fetch User B Next Action Card -> 403 Forbidden
    rec_res = await async_client.get(f"/api/v1/projects/{pj_b_id}/recommendations/next-action", headers=headers_a)
    assert rec_res.status_code == 403

    # User A attempts to fetch User B project analytics -> 403 Forbidden
    analytics_res = await async_client.get(f"/api/v1/analytics/project/{pj_b_id}", headers=headers_a)
    assert analytics_res.status_code == 403


@pytest.mark.asyncio
async def test_prd_section_30_student_data_isolation(async_client: AsyncClient):
    """PRD Section 30 Data Isolation test:
    Verifies that Student A listing projects receives ONLY Student A's projects (RAG, LLM Fine-Tuning, Advanced Python)
    and NEVER receives Student B's projects (SQL) or Student C's projects (Cryptography).
    """
    from app.core.seed import seed_demo_data
    await seed_demo_data()

    auth_service = AuthService()

    from app.modules.auth.schemas import LoginRequest

    # Login as Student A (varshitha@example.com)
    student_a = await auth_service.login(LoginRequest(email="varshitha@example.com", password="password123"))
    headers_a = {"Authorization": f"Bearer {student_a.access_token}"}

    # Login as Student B (studentb@example.com)
    student_b = await auth_service.login(LoginRequest(email="studentb@example.com", password="password123"))
    headers_b = {"Authorization": f"Bearer {student_b.access_token}"}

    # Student A queries GET /api/v1/projects
    res_a = await async_client.get("/api/v1/projects", headers=headers_a)
    assert res_a.status_code == 200
    items_a = res_a.json()["data"]["items"]
    names_a = [p["name"] for p in items_a]

    # Verify Student A sees ONLY Student A projects
    assert "RAG Fundamentals" in names_a or "LLM Fine-Tuning" in names_a or "Advanced Python" in names_a
    assert "SQL Mastery" not in names_a
    assert "Cryptography" not in names_a

    # Student B queries GET /api/v1/projects
    res_b = await async_client.get("/api/v1/projects", headers=headers_b)
    assert res_b.status_code == 200
    items_b = res_b.json()["data"]["items"]
    names_b = [p["name"] for p in items_b]

    # Verify Student B sees ONLY Student B projects
    assert "SQL Mastery" in names_b or "DSA Interview Preparation" in names_b
    assert "RAG Fundamentals" not in names_b
    assert "Cryptography" not in names_b

