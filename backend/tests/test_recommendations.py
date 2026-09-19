import uuid
import pytest
from httpx import AsyncClient

from app.modules.events.schemas import LearningEventCreate
from app.modules.events.service import EventService
from app.modules.recommendations.engine import RecommendationRankingEngine


def test_recommendation_ranking_engine_relevance():
    candidates = RecommendationRankingEngine.generate_candidate_recommendations(
        weak_concepts=["Raft Consensus"],
        mastery_list=[{"concept_id": "Raft Consensus", "mastery_score": 0.40}],
        recent_mistakes=[{"concept_id": "Raft Consensus"}],
        materials_count=2,
    )
    assert len(candidates) >= 3
    # Top candidate should be mistake review or weak concept practice
    assert candidates[0]["priority_score"] >= 0.70
    assert "Raft Consensus" in candidates[0]["title"]


@pytest.mark.asyncio
async def test_event_recording_idempotency_and_workflow(async_client: AsyncClient):
    # 1. Signup, space & project setup
    u_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "rec_user@example.com", "password": "password123"},
    )
    token = u_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    sp = await async_client.post("/api/v1/spaces", json={"name": "Rec Space", "slug": "rec-space"}, headers=headers)
    pj = await async_client.post("/api/v1/projects", json={"space_id": sp.json()["data"]["id"], "name": "Rec Project"}, headers=headers)
    pj_id = pj.json()["data"]["id"]

    # 2. Record durable learning event
    service = EventService()
    req = LearningEventCreate(
        project_id=pj_id,
        event_type="quiz_completed",
        payload={"score_percentage": 50.0, "weak_concepts": ["Concurrency"]},
        idempotency_key="evt-rec-flow-101",
    )
    user_uuid = uuid.UUID(u_resp.json()["data"]["user"]["id"])
    evt_resp = await service.record_event(user_id=user_uuid, req=req)
    assert evt_resp.status == "processed"
    assert evt_resp.idempotency_key == "evt-rec-flow-101"

    # 3. Duplicate event idempotency test (re-sending same key should be safely ignored)
    evt_dup = await service.record_event(user_id=user_uuid, req=req)
    assert evt_dup.id == evt_resp.id

    # 4. Fetch Next Action Card via REST API
    next_card = await async_client.get(f"/api/v1/projects/{pj_id}/recommendations/next-action", headers=headers)
    assert next_card.status_code == 200
    card_data = next_card.json()["data"]
    assert card_data["cta_label"] is not None
    assert card_data["recommendation"] is not None

    # 5. Complete recommendation action
    rec_id = card_data["recommendation"]["id"]
    comp_res = await async_client.post(
        f"/api/v1/projects/{pj_id}/recommendations/{rec_id}/complete", headers=headers
    )
    assert comp_res.status_code == 200
    assert comp_res.json()["data"]["status"] == "completed"


@pytest.mark.asyncio
async def test_recommendations_project_isolation(async_client: AsyncClient):
    # User 1 creates project & recommendations
    u1_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "rec_iso1@example.com", "password": "password123"},
    )
    h1 = {"Authorization": f"Bearer {u1_resp.json()['data']['access_token']}"}
    sp1 = await async_client.post("/api/v1/spaces", json={"name": "S1", "slug": "s1-rec"}, headers=h1)
    pj1 = await async_client.post("/api/v1/projects", json={"space_id": sp1.json()["data"]["id"], "name": "P1"}, headers=h1)
    pj1_id = pj1.json()["data"]["id"]

    # User 2 attempts to fetch User 1 recommendation card -> 403 / 404
    u2_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "rec_iso2@example.com", "password": "password123"},
    )
    h2 = {"Authorization": f"Bearer {u2_resp.json()['data']['access_token']}"}

    unauth_res = await async_client.get(f"/api/v1/projects/{pj1_id}/recommendations/next-action", headers=h2)
    assert unauth_res.status_code in (403, 404)
