import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_and_me_flow(async_client: AsyncClient):
    signup_payload = {
        "email": "student_test@example.com",
        "password": "securepassword123",
        "full_name": "Test Student",
    }
    response = await async_client.post("/api/v1/auth/signup", json=signup_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    token = data["data"]["access_token"]
    assert data["data"]["user"]["email"] == "student_test@example.com"

    # Test GET /me with token
    me_resp = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["success"] is True
    assert me_data["data"]["email"] == "student_test@example.com"


@pytest.mark.asyncio
async def test_login_flow(async_client: AsyncClient):
    # Signup user first
    signup_payload = {
        "email": "login_test@example.com",
        "password": "mypassword123",
        "full_name": "Login User",
    }
    await async_client.post("/api/v1/auth/signup", json=signup_payload)

    # Login with valid credentials
    login_payload = {
        "email": "login_test@example.com",
        "password": "mypassword123",
    }
    resp = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert resp.status_code == 200
    json_data = resp.json()
    assert json_data["success"] is True
    assert "access_token" in json_data["data"]

    # Login with invalid password
    invalid_login = {
        "email": "login_test@example.com",
        "password": "wrongpassword",
    }
    bad_resp = await async_client.post("/api/v1/auth/login", json=invalid_login)
    assert bad_resp.status_code == 401
    assert bad_resp.json()["success"] is False
    assert bad_resp.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_duplicate_email_signup(async_client: AsyncClient):
    payload = {
        "email": "dup@example.com",
        "password": "password123",
    }
    r1 = await async_client.post("/api/v1/auth/signup", json=payload)
    assert r1.status_code == 201

    r2 = await async_client.post("/api/v1/auth/signup", json=payload)
    assert r2.status_code == 400
    assert r2.json()["error"]["code"] == "EMAIL_EXISTS"


@pytest.mark.asyncio
async def test_database_password_persistence(async_client: AsyncClient):
    from app.modules.auth.service import _IN_MEMORY_USERS
    signup_payload = {
        "email": "db_persist_user@example.com",
        "password": "dbpassword123",
        "full_name": "Database User",
    }
    r = await async_client.post("/api/v1/auth/signup", json=signup_payload)
    assert r.status_code == 201

    # Clear in-memory cache to simulate server restart / fresh database lookup
    _IN_MEMORY_USERS.pop("db_persist_user@example.com", None)

    # Login should successfully verify password against database record
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "db_persist_user@example.com", "password": "dbpassword123"},
    )
    assert login_resp.status_code == 200
    assert login_resp.json()["success"] is True

    # Login with wrong password should fail even when querying DB
    _IN_MEMORY_USERS.pop("db_persist_user@example.com", None)
    wrong_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "db_persist_user@example.com", "password": "wrongpassword"},
    )
    assert wrong_resp.status_code == 401

