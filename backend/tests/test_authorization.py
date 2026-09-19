import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_unauthenticated_access_denied(async_client: AsyncClient):
    """Verify missing Authorization header returns 401 Unauthorized."""
    response = await async_client.get("/api/v1/spaces")
    assert response.status_code == 401
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_invalid_bearer_token(async_client: AsyncClient):
    """Verify invalid or malformed token returns 401 Unauthorized."""
    response = await async_client.get(
        "/api/v1/spaces", headers={"Authorization": "Bearer invalid_garbage_token"}
    )
    assert response.status_code == 401
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_space_access_authorization(async_client: AsyncClient):
    """Verify user can access own space, but is denied access to unauthorized space."""
    # Register User A
    u1_signup = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "user_a@example.com", "password": "password123"},
    )
    t1 = u1_signup.json()["data"]["access_token"]

    # User A creates Space A
    sp1 = await async_client.post(
        "/api/v1/spaces",
        json={"name": "Space A", "slug": "space-a"},
        headers={"Authorization": f"Bearer {t1}"},
    )
    assert sp1.status_code == 201
    space_a_id = sp1.json()["data"]["id"]

    # User A can access Space A
    acc1 = await async_client.get(
        f"/api/v1/spaces/{space_a_id}",
        headers={"Authorization": f"Bearer {t1}"},
    )
    assert acc1.status_code == 200
    assert acc1.json()["data"]["id"] == space_a_id
    assert acc1.json()["data"]["name"] == "Space A"

    # Register User B
    u2_signup = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "user_b@example.com", "password": "password123"},
    )
    t2 = u2_signup.json()["data"]["access_token"]

    # User B attempts to access Space A -> 403 Forbidden
    acc2 = await async_client.get(
        f"/api/v1/spaces/{space_a_id}",
        headers={"Authorization": f"Bearer {t2}"},
    )
    assert acc2.status_code == 403
    assert acc2.json()["success"] is False
    assert acc2.json()["error"]["code"] == "TENANT_ACCESS_DENIED"


@pytest.mark.asyncio
async def test_nonexistent_space_denied(async_client: AsyncClient):
    """Verify accessing a non-existent space returns 403 TenantAccessDeniedError."""
    u_signup = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "random@example.com", "password": "password123"},
    )
    token = u_signup.json()["data"]["access_token"]
    random_space_id = str(uuid.uuid4())

    resp = await async_client.get(
        f"/api/v1/spaces/{random_space_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "TENANT_ACCESS_DENIED"


@pytest.mark.asyncio
async def test_duplicate_space_slug_denied(async_client: AsyncClient):
    """Verify creating a space with an existing slug returns 400 Bad Request."""
    u_signup = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "slug_user@example.com", "password": "password123"},
    )
    token = u_signup.json()["data"]["access_token"]

    r1 = await async_client.post(
        "/api/v1/spaces",
        json={"name": "Unique Space", "slug": "unique-slug"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r1.status_code == 201

    r2 = await async_client.post(
        "/api/v1/spaces",
        json={"name": "Duplicate Space", "slug": "unique-slug"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 400
    assert r2.json()["error"]["code"] == "SLUG_EXISTS"


@pytest.mark.asyncio
async def test_admin_endpoint_rbac(async_client: AsyncClient):
    """Verify student account is denied admin endpoints (403), while admin account is permitted (200)."""
    # Student account signup
    student_signup = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "student_rbac@example.com", "password": "password123", "full_name": "Student User"},
    )
    student_token = student_signup.json()["data"]["access_token"]
    assert student_signup.json()["data"]["user"]["role"] == "user"
    assert student_signup.json()["data"]["user"]["is_admin"] is False

    # Student attempts to access admin endpoint -> 403 Forbidden
    resp = await async_client.get(
        "/api/v1/admin/overview",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp.status_code == 403
    assert resp.json()["success"] is False
    assert resp.json()["error"]["code"] == "TENANT_ACCESS_DENIED"

    # Admin account signup (email starting with admin@ automatically gets admin role)
    admin_signup = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "admin_test@example.com", "password": "adminpassword123", "full_name": "Admin User"},
    )
    assert admin_signup.status_code in (200, 201)
    admin_token = admin_signup.json()["data"]["access_token"]
    assert admin_signup.json()["data"]["user"]["role"] == "admin"
    assert admin_signup.json()["data"]["user"]["is_admin"] is True

    # Admin accesses admin endpoint -> 200 OK
    admin_resp = await async_client.get(
        "/api/v1/admin/overview",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_resp.status_code == 200
    assert "total_users" in admin_resp.json()
