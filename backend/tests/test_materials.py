import fitz  # PyMuPDF
import pytest
from httpx import AsyncClient


def create_sample_pdf_bytes(title: str = "Test Document", content: str = "Hello World") -> bytes:
    """Helper generating valid sample PDF bytes using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), f"{title}\n{content}")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.mark.asyncio
async def test_upload_valid_pdf_success(async_client: AsyncClient):
    # 1. Signup user, create space and project
    user_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "mat_owner@example.com", "password": "password123"},
    )
    assert user_resp.status_code == 201
    token = user_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    sp = await async_client.post(
        "/api/v1/spaces", json={"name": "Mat Space", "slug": "mat-space"}, headers=headers
    )
    sp_id = sp.json()["data"]["id"]

    pj = await async_client.post(
        "/api/v1/projects", json={"space_id": sp_id, "name": "Mat Project"}, headers=headers
    )
    pj_id = pj.json()["data"]["id"]

    # 2. Upload sample PDF
    pdf_bytes = create_sample_pdf_bytes("Quantum Mechanics Notes", "Wave functions and state vectors.")
    files = {"file": ("quantum.pdf", pdf_bytes, "application/pdf")}

    upload_resp = await async_client.post(
        f"/api/v1/projects/{pj_id}/materials",
        files=files,
        headers=headers,
    )
    assert upload_resp.status_code == 201
    mat_data = upload_resp.json()["data"]
    mat_id = mat_data["id"]

    assert mat_data["filename"] == "quantum.pdf"
    assert mat_data["status"] == "ready"
    assert mat_data["page_count"] == 1
    assert mat_data["attempt_count"] == 1
    assert mat_data["checksum"] is not None

    # 3. Get Extracted Pages
    pages_resp = await async_client.get(
        f"/api/v1/materials/{mat_id}/pages",
        headers=headers,
    )
    assert pages_resp.status_code == 200
    pages_data = pages_resp.json()["data"]
    assert pages_data["total"] == 1
    assert "Quantum Mechanics Notes" in pages_data["items"][0]["extracted_text"]


@pytest.mark.asyncio
async def test_upload_invalid_file_rejected(async_client: AsyncClient):
    user_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "inv_mat@example.com", "password": "password123"},
    )
    token = user_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    sp = await async_client.post(
        "/api/v1/spaces", json={"name": "Inv Space", "slug": "inv-space"}, headers=headers
    )
    sp_id = sp.json()["data"]["id"]

    pj = await async_client.post(
        "/api/v1/projects", json={"space_id": sp_id, "name": "Inv Project"}, headers=headers
    )
    pj_id = pj.json()["data"]["id"]

    # Upload non-PDF text file disguised as PDF
    bad_files = {"file": ("fake.pdf", b"PLAIN TEXT CONTENT NOT PDF", "application/pdf")}
    res = await async_client.post(
        f"/api/v1/projects/{pj_id}/materials",
        files=bad_files,
        headers=headers,
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_FILE_TYPE"


@pytest.mark.asyncio
async def test_upload_oversized_file_rejected(async_client: AsyncClient):
    user_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "over_mat@example.com", "password": "password123"},
    )
    token = user_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    sp = await async_client.post(
        "/api/v1/spaces", json={"name": "Over Space", "slug": "over-space"}, headers=headers
    )
    sp_id = sp.json()["data"]["id"]

    pj = await async_client.post(
        "/api/v1/projects", json={"space_id": sp_id, "name": "Over Project"}, headers=headers
    )
    pj_id = pj.json()["data"]["id"]

    # Generate oversized content (> 25MB) starting with %PDF
    oversized_bytes = b"%PDF-1.4 " + b"0" * (26 * 1024 * 1024)
    res = await async_client.post(
        f"/api/v1/projects/{pj_id}/materials",
        files={"file": ("huge.pdf", oversized_bytes, "application/pdf")},
        headers=headers,
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "FILE_OVERSIZED"


@pytest.mark.asyncio
async def test_duplicate_file_checksum_detection(async_client: AsyncClient):
    user_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "dup_mat@example.com", "password": "password123"},
    )
    token = user_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    sp = await async_client.post(
        "/api/v1/spaces", json={"name": "Dup Space", "slug": "dup-space"}, headers=headers
    )
    sp_id = sp.json()["data"]["id"]

    pj = await async_client.post(
        "/api/v1/projects", json={"space_id": sp_id, "name": "Dup Project"}, headers=headers
    )
    pj_id = pj.json()["data"]["id"]

    pdf_bytes = create_sample_pdf_bytes("Duplicate Test", "Identical bytes content.")

    # Upload 1
    res1 = await async_client.post(
        f"/api/v1/projects/{pj_id}/materials",
        files={"file": ("file1.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert res1.status_code == 201
    mat1_id = res1.json()["data"]["id"]

    # Upload 2 with same content bytes
    res2 = await async_client.post(
        f"/api/v1/projects/{pj_id}/materials",
        files={"file": ("file1_copy.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert res2.status_code == 201
    mat2_id = res2.json()["data"]["id"]

    # Duplicate detected -> returns existing material record
    assert mat1_id == mat2_id


@pytest.mark.asyncio
async def test_retry_and_idempotent_page_replacement(async_client: AsyncClient):
    user_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "retry_mat@example.com", "password": "password123"},
    )
    token = user_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    sp = await async_client.post(
        "/api/v1/spaces", json={"name": "Retry Space", "slug": "retry-space"}, headers=headers
    )
    sp_id = sp.json()["data"]["id"]

    pj = await async_client.post(
        "/api/v1/projects", json={"space_id": sp_id, "name": "Retry Project"}, headers=headers
    )
    pj_id = pj.json()["data"]["id"]

    pdf_bytes = create_sample_pdf_bytes("Retry Doc", "Testing retry idempotency.")
    up_res = await async_client.post(
        f"/api/v1/projects/{pj_id}/materials",
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    mat_id = up_res.json()["data"]["id"]
    assert up_res.json()["data"]["attempt_count"] in (0, 1)

    # Trigger manual retry
    retry_res = await async_client.post(
        f"/api/v1/materials/{mat_id}/retry",
        headers=headers,
    )
    assert retry_res.status_code == 200
    assert retry_res.json()["data"]["attempt_count"] in (1, 2, 3)

    # Verify pages are NOT duplicated
    pages_res = await async_client.get(
        f"/api/v1/materials/{mat_id}/pages",
        headers=headers,
    )
    assert pages_res.json()["data"]["total"] == 1


@pytest.mark.asyncio
async def test_material_ownership_isolation(async_client: AsyncClient):
    # User 1 creates material
    u1_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "iso_u1@example.com", "password": "password123"},
    )
    t1 = u1_resp.json()["data"]["access_token"]
    h1 = {"Authorization": f"Bearer {t1}"}

    sp1 = await async_client.post("/api/v1/spaces", json={"name": "U1 Mat Space", "slug": "u1-mat-space"}, headers=h1)
    sp1_id = sp1.json()["data"]["id"]

    pj1 = await async_client.post("/api/v1/projects", json={"space_id": sp1_id, "name": "U1 Mat Project"}, headers=h1)
    pj1_id = pj1.json()["data"]["id"]

    pdf_bytes = create_sample_pdf_bytes("Secret U1 Doc", "Top secret information.")
    up1 = await async_client.post(
        f"/api/v1/projects/{pj1_id}/materials",
        files={"file": ("secret.pdf", pdf_bytes, "application/pdf")},
        headers=h1,
    )
    mat1_id = up1.json()["data"]["id"]

    # User 2 signup
    u2_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "iso_u2@example.com", "password": "password123"},
    )
    t2 = u2_resp.json()["data"]["access_token"]
    h2 = {"Authorization": f"Bearer {t2}"}

    # User 2 attempts to list User 1 project materials -> 403 Forbidden
    unauth_list = await async_client.get(f"/api/v1/projects/{pj1_id}/materials", headers=h2)
    assert unauth_list.status_code == 403

    # User 2 attempts to get User 1 material details -> 403 Forbidden
    unauth_get = await async_client.get(f"/api/v1/materials/{mat1_id}", headers=h2)
    assert unauth_get.status_code == 403

    # User 2 attempts to get User 1 material pages -> 403 Forbidden
    unauth_pages = await async_client.get(f"/api/v1/materials/{mat1_id}/pages", headers=h2)
    assert unauth_pages.status_code == 403

    # User 2 attempts to trigger retry on User 1 material -> 403 Forbidden
    unauth_retry = await async_client.post(f"/api/v1/materials/{mat1_id}/retry", headers=h2)
    assert unauth_retry.status_code == 403
