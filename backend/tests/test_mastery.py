import pytest
from httpx import AsyncClient

from app.modules.mastery.engine import DeterministicMasteryEngine


def test_deterministic_mastery_calculation_improvement():
    # 1. Baseline new concept
    new_m, delta, status, ev = DeterministicMasteryEngine.calculate_new_mastery(
        previous_mastery=0.0, score_percentage=100.0, difficulty="intermediate"
    )
    assert new_m == 1.0
    assert status == "improving"

    # 2. Sequential improvement
    m2, delta2, status2, _ = DeterministicMasteryEngine.calculate_new_mastery(
        previous_mastery=0.5, score_percentage=90.0, difficulty="advanced", alpha=0.3
    )
    assert m2 > 0.5
    assert delta2 > 0.0
    assert status2 == "improving"


def test_mastery_calculation_repeated_mistakes_penalty():
    # Performance with repeated mistakes penalty
    m, delta, status, ev = DeterministicMasteryEngine.calculate_new_mastery(
        previous_mastery=0.8,
        score_percentage=40.0,
        difficulty="intermediate",
        repeated_mistakes_count=2,  # penalty of 0.2
    )
    assert m < 0.8
    assert delta < 0.0
    assert status == "requiring_attention"
    assert ev["mistake_penalty_applied"] == 0.2


def test_explainability_generation():
    exp = DeterministicMasteryEngine.generate_explanation(
        concept_id="Raft Consensus",
        current_mastery=0.85,
        previous_mastery=0.70,
        delta=0.15,
        status="improving",
        recent_events=[
            {
                "timestamp": "2026-09-17T00:00:00Z",
                "evidence": {"score_percentage": 95.0, "difficulty": "advanced"},
            }
        ],
    )
    assert "Raft Consensus" in exp.explanation
    assert exp.status == "improving"
    assert exp.current_mastery == 0.85


@pytest.mark.asyncio
async def test_mastery_flow_idempotency_and_snapshots(async_client: AsyncClient):
    # 1. Signup, space & project setup
    u_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "m_user@example.com", "password": "password123"},
    )
    token = u_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    sp = await async_client.post("/api/v1/spaces", json={"name": "Mastery Space", "slug": "mastery-space"}, headers=headers)
    pj = await async_client.post("/api/v1/projects", json={"space_id": sp.json()["data"]["id"], "name": "Mastery Project"}, headers=headers)
    pj_id = pj.json()["data"]["id"]

    # 2. List initial masteries
    list_res = await async_client.get(f"/api/v1/projects/{pj_id}/mastery", headers=headers)
    assert list_res.status_code == 200
    masteries = list_res.json()["data"]
    assert len(masteries) >= 1

    # 3. Record Event 1
    evt1 = await async_client.post(
        f"/api/v1/projects/{pj_id}/mastery/Raft/record",
        json={
            "score_percentage": 90.0,
            "difficulty": "advanced",
            "event_id": "evt-unique-101",
        },
        headers=headers,
    )
    assert evt1.status_code == 200
    m_data = evt1.json()["data"]
    assert m_data["mastery_score"] > 0.0

    # 4. Duplicate Event Idempotency Defense check (should not alter score)
    evt1_dup = await async_client.post(
        f"/api/v1/projects/{pj_id}/mastery/Raft/record",
        json={
            "score_percentage": 90.0,
            "difficulty": "advanced",
            "event_id": "evt-unique-101",
        },
        headers=headers,
    )
    assert evt1_dup.status_code == 200
    assert evt1_dup.json()["data"]["mastery_score"] == m_data["mastery_score"]

    # 5. Fetch Explainability Payload ('Why did this change?')
    exp_res = await async_client.get(f"/api/v1/projects/{pj_id}/mastery/Raft/explanation", headers=headers)
    assert exp_res.status_code == 200
    exp_data = exp_res.json()["data"]
    assert exp_data["concept_id"] == "Raft"
    assert "explanation" in exp_data

    # 6. Fetch Growth Summary & Snapshots
    sum_res = await async_client.get(f"/api/v1/projects/{pj_id}/growth/summary", headers=headers)
    assert sum_res.status_code == 200
    assert sum_res.json()["data"]["has_sufficient_data"] is True

    snap_res = await async_client.get(f"/api/v1/projects/{pj_id}/growth/snapshots", headers=headers)
    assert snap_res.status_code == 200
    assert len(snap_res.json()["data"]) >= 1


@pytest.mark.asyncio
async def test_mastery_project_isolation(async_client: AsyncClient):
    # User 1 creates project
    u1_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "m_iso1@example.com", "password": "password123"},
    )
    h1 = {"Authorization": f"Bearer {u1_resp.json()['data']['access_token']}"}
    sp1 = await async_client.post("/api/v1/spaces", json={"name": "S1", "slug": "s1-mst"}, headers=h1)
    pj1 = await async_client.post("/api/v1/projects", json={"space_id": sp1.json()["data"]["id"], "name": "P1"}, headers=h1)
    pj1_id = pj1.json()["data"]["id"]

    # User 2 attempts to query User 1 project mastery -> 403 / 404
    u2_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "m_iso2@example.com", "password": "password123"},
    )
    h2 = {"Authorization": f"Bearer {u2_resp.json()['data']['access_token']}"}

    unauth_res = await async_client.get(f"/api/v1/projects/{pj1_id}/mastery", headers=h2)
    assert unauth_res.status_code in (403, 404)
