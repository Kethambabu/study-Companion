import os
import uuid
import pytest
from httpx import AsyncClient

from tests.test_materials import create_sample_pdf_bytes


@pytest.mark.asyncio
async def test_full_learner_lifecycle_end_to_end(async_client: AsyncClient):
    suffix = uuid.uuid4().hex[:8]
    dynamic_email = f"e2e_learner_{suffix}@example.com"
    dynamic_slug = f"e2e-study-space-{suffix}"
    print("\n[E2E STEP 1] Signup User & Create Tenant Space...")
    u_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": dynamic_email, "password": "Password123!", "full_name": "E2E Learner"},
    )
    assert u_resp.status_code == 201
    token = u_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    sp_resp = await async_client.post(
        "/api/v1/spaces",
        json={"name": f"E2E Study Space {suffix}", "slug": dynamic_slug},
        headers=headers,
    )
    assert sp_resp.status_code == 201
    space_id = sp_resp.json()["data"]["id"]

    print("[E2E STEP 2] Create Project & Upload PDF Material...")
    pj_resp = await async_client.post(
        "/api/v1/projects",
        json={"space_id": space_id, "name": "Distributed Systems Engineering"},
        headers=headers,
    )
    assert pj_resp.status_code == 201
    project_id = pj_resp.json()["data"]["id"]

    pdf_text = "The Paxos protocol guarantees consensus across unreliable asynchronous networks using two phases: Prepare and Accept."
    pdf_bytes = create_sample_pdf_bytes("Paxos Protocol", pdf_text)

    mat_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/materials",
        files={"file": ("paxos_notes.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert mat_resp.status_code == 201
    material_id = mat_resp.json()["data"]["id"]

    print("[E2E STEP 3] Process & Index Document Chunks...")
    idx_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/knowledge/index/{material_id}",
        headers=headers,
    )
    assert idx_resp.status_code == 200
    assert idx_resp.json()["data"]["chunks_indexed"] >= 1

    print("[E2E STEP 4] AI Tutor Grounded Chat Session...")
    conv_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/tutor/conversations",
        json={"title": "Paxos Deep Dive"},
        headers=headers,
    )
    assert conv_resp.status_code == 201
    conv_id = conv_resp.json()["data"]["id"]

    msg_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/tutor/conversations/{conv_id}/messages",
        json={"content": "Explain how Paxos guarantees consensus", "mode": "default"},
        headers=headers,
    )
    assert msg_resp.status_code == 200
    assert msg_resp.json()["data"]["confidence_status"] == "grounded"

    print("[E2E STEP 5] Adaptive Assessment Quiz Creation & Attempt Submission...")
    quiz_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/quizzes",
        json={"title": "Paxos Quiz", "num_questions": 3, "question_types": ["mcq"], "difficulty": "intermediate"},
        headers=headers,
    )
    assert quiz_resp.status_code == 201
    quiz = quiz_resp.json()["data"]
    quiz_id = quiz["id"]

    att_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/quizzes/{quiz_id}/attempts",
        headers=headers,
    )
    assert att_resp.status_code == 200

    print("[E2E STEP 6] Concept Mastery Update & Growth Summary...")
    mastery_resp = await async_client.get(
        f"/api/v1/projects/{project_id}/growth/summary",
        headers=headers,
    )
    assert mastery_resp.status_code == 200
    assert mastery_resp.json()["data"]["overall_mastery"] >= 0.0

    print("[E2E STEP 7] Next Action Card & Recommendation Generation...")
    rec_resp = await async_client.get(
        f"/api/v1/projects/{project_id}/recommendations/next-action",
        headers=headers,
    )
    assert rec_resp.status_code == 200
    assert rec_resp.json()["data"]["cta_label"] is not None

    print("[E2E STEP 8] Global Analytics Aggregation...")
    analytics_resp = await async_client.get(
        "/api/v1/analytics/global",
        headers=headers,
    )
    assert analytics_resp.status_code == 200
    assert analytics_resp.json()["total_users"] >= 1

    print("\n[SUCCESS] E2E Learner Lifecycle Completed Seamlessly!")
