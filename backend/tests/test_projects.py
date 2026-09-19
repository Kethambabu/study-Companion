import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_project_crud_and_archiving_flow(async_client: AsyncClient):
    # 1. Signup & get token
    signup_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "project_owner@example.com", "password": "password123"},
    )
    assert signup_resp.status_code == 201
    token = signup_resp.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Space
    sp_resp = await async_client.post(
        "/api/v1/spaces",
        json={"name": "Physics Space", "slug": "physics-space"},
        headers=auth_headers,
    )
    assert sp_resp.status_code == 201
    space_id = sp_resp.json()["data"]["id"]

    # 3. Create Project inside Space
    proj_resp = await async_client.post(
        "/api/v1/projects",
        json={
            "space_id": space_id,
            "name": "Quantum Mechanics",
            "description": "Introductory quantum theory and wave equations.",
            "learning_goal": "Master wave functions and Schrodinger equation.",
        },
        headers=auth_headers,
    )
    assert proj_resp.status_code == 201
    proj_data = proj_resp.json()["data"]
    project_id = proj_data["id"]
    assert proj_data["name"] == "Quantum Mechanics"
    assert proj_data["status"] == "active"

    # 4. Get Project Details
    get_resp = await async_client.get(
        f"/api/v1/projects/{project_id}", headers=auth_headers
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["learning_goal"] == "Master wave functions and Schrodinger equation."

    # 5. Update Project
    patch_resp = await async_client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "Advanced Quantum Mechanics"},
        headers=auth_headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["data"]["name"] == "Advanced Quantum Mechanics"

    # 6. List Projects scoped to Space
    list_resp = await async_client.get(
        f"/api/v1/projects?space_id={space_id}", headers=auth_headers
    )
    assert list_resp.status_code == 200
    paged = list_resp.json()["data"]
    assert paged["total"] == 1
    assert paged["items"][0]["id"] == project_id

    # 7. Archive Project
    del_resp = await async_client.delete(
        f"/api/v1/projects/{project_id}", headers=auth_headers
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["data"]["status"] == "archived"
    assert del_resp.json()["data"]["archived_at"] is not None


@pytest.mark.asyncio
async def test_project_space_isolation(async_client: AsyncClient):
    # User 1 creates Space 1 and Project 1
    u1_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "u1_proj@example.com", "password": "password123"},
    )
    t1 = u1_resp.json()["data"]["access_token"]
    h1 = {"Authorization": f"Bearer {t1}"}

    sp1 = await async_client.post(
        "/api/v1/spaces",
        json={"name": "U1 Space", "slug": "u1-space"},
        headers=h1,
    )
    sp1_id = sp1.json()["data"]["id"]

    p1 = await async_client.post(
        "/api/v1/projects",
        json={"space_id": sp1_id, "name": "Secret Project U1"},
        headers=h1,
    )
    p1_id = p1.json()["data"]["id"]

    # User 2 signup
    u2_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "u2_proj@example.com", "password": "password123"},
    )
    t2 = u2_resp.json()["data"]["access_token"]
    h2 = {"Authorization": f"Bearer {t2}"}

    # User 2 attempts to get Project 1 -> 403 Forbidden
    unauth_resp = await async_client.get(
        f"/api/v1/projects/{p1_id}", headers=h2
    )
    assert unauth_resp.status_code == 403
    assert unauth_resp.json()["error"]["code"] == "TENANT_ACCESS_DENIED"

    # User 2 attempts to create project in Space 1 -> 403 Forbidden
    unauth_create = await async_client.post(
        "/api/v1/projects",
        json={"space_id": sp1_id, "name": "Unauthorized Project"},
        headers=h2,
    )
    assert unauth_create.status_code == 403


@pytest.mark.asyncio
async def test_invalid_project_status_update(async_client: AsyncClient):
    u_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "val_user@example.com", "password": "password123"},
    )
    token = u_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    sp = await async_client.post(
        "/api/v1/spaces", json={"name": "Val Space", "slug": "val-space"}, headers=headers
    )
    sp_id = sp.json()["data"]["id"]

    p = await async_client.post(
        "/api/v1/projects", json={"space_id": sp_id, "name": "Test P"}, headers=headers
    )
    p_id = p.json()["data"]["id"]

    # Invalid status update -> 422 Unprocessable Entity
    bad_status = await async_client.patch(
        f"/api/v1/projects/{p_id}",
        json={"status": "invalid_status_enum"},
        headers=headers,
    )
    assert bad_status.status_code == 422
    assert bad_status.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_project_list_multi_tenant_isolation(async_client: AsyncClient):
    # User 1 creates space and project
    u1_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "u1_list_iso@example.com", "password": "password123"},
    )
    h1 = {"Authorization": f"Bearer {u1_resp.json()['data']['access_token']}"}
    sp1 = await async_client.post("/api/v1/spaces", json={"name": "U1 Private Space", "slug": "u1-p-space"}, headers=h1)
    sp1_id = sp1.json()["data"]["id"]
    await async_client.post("/api/v1/projects", json={"space_id": sp1_id, "name": "U1 Secret Proj"}, headers=h1)

    # User 2 creates space and project
    u2_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "u2_list_iso@example.com", "password": "password123"},
    )
    h2 = {"Authorization": f"Bearer {u2_resp.json()['data']['access_token']}"}
    sp2 = await async_client.post("/api/v1/spaces", json={"name": "U2 Space", "slug": "u2-space"}, headers=h2)
    sp2_id = sp2.json()["data"]["id"]
    await async_client.post("/api/v1/projects", json={"space_id": sp2_id, "name": "U2 Proj"}, headers=h2)

    # User 2 lists projects -> should only see User 2's project
    list_u2 = await async_client.get("/api/v1/projects", headers=h2)
    assert list_u2.status_code == 200
    u2_items = list_u2.json()["data"]["items"]
    assert len(u2_items) == 1
    assert u2_items[0]["name"] == "U2 Proj"

