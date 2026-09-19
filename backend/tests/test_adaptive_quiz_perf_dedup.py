import time
import pytest
from httpx import AsyncClient

from app.modules.assessment.generator import QuestionGenerator, compute_question_fingerprint


@pytest.mark.asyncio
async def test_adaptive_quiz_start_and_evaluate_latency(async_client: AsyncClient):
    """Verifies that quiz creation and answer evaluation complete well within 2 seconds."""
    # 1. Signup & Project setup
    u_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "perf_test_user@example.com", "password": "password123"},
    )
    assert u_resp.status_code == 201
    token = u_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    sp_res = await async_client.post("/api/v1/spaces", json={"name": "Perf Space", "slug": "perf-space"}, headers=headers)
    assert sp_res.status_code == 201
    sp_id = sp_res.json()["data"]["id"]

    pj_res = await async_client.post("/api/v1/projects", json={"space_id": sp_id, "name": "Perf Project"}, headers=headers)
    assert pj_res.status_code == 201
    pj_id = pj_res.json()["data"]["id"]

    # 2. Benchmark Quiz Creation Time (< 2.0s target)
    t0 = time.perf_counter()
    qz_res = await async_client.post(
        f"/api/v1/projects/{pj_id}/quizzes",
        json={"num_questions": 10, "difficulty_preference": "adaptive"},
        headers=headers,
    )
    create_duration = time.perf_counter() - t0
    assert qz_res.status_code == 201
    assert create_duration < 2.0, f"Quiz start duration ({create_duration:.3f}s) exceeded 2.0 second limit!"

    qz_data = qz_res.json()["data"]
    qz_id = qz_data["id"]
    questions = qz_data["questions"]
    assert len(questions) == 10

    # 3. Start attempt
    att_res = await async_client.post(f"/api/v1/projects/{pj_id}/quizzes/{qz_id}/attempts", headers=headers)
    assert att_res.status_code == 200
    att_id = att_res.json()["data"]["attempt"]["id"]

    # 4. Benchmark Answer Evaluation Time (< 2.0s target)
    q1 = questions[0]
    ans_text = q1["options"][0] if q1.get("options") else "Thorough explanation of the core concept mechanism."

    t_eval0 = time.perf_counter()
    sub_res = await async_client.post(
        f"/api/v1/projects/{pj_id}/quizzes/{qz_id}/attempts/{att_id}/questions/{q1['id']}/submit",
        json={"user_answer": ans_text},
        headers=headers,
    )
    eval_duration = time.perf_counter() - t_eval0
    assert sub_res.status_code == 200
    assert eval_duration < 2.0, f"Answer evaluation duration ({eval_duration:.3f}s) exceeded 2.0 second limit!"


@pytest.mark.asyncio
async def test_zero_question_repetition_across_multiple_quizzes(async_client: AsyncClient):
    """Verifies 0% question repetition across 5 consecutive 10-question adaptive quizzes."""
    u_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "dedup_test_user@example.com", "password": "password123"},
    )
    token = u_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    sp_res = await async_client.post("/api/v1/spaces", json={"name": "Dedup Space", "slug": "dedup-space"}, headers=headers)
    sp_id = sp_res.json()["data"]["id"]

    pj_res = await async_client.post("/api/v1/projects", json={"space_id": sp_id, "name": "Dedup Project"}, headers=headers)
    pj_id = pj_res.json()["data"]["id"]

    seen_fingerprints = set()
    total_questions = 0
    duplicate_count = 0

    # Generate 5 consecutive adaptive quizzes (10 questions each = 50 total questions)
    for qz_idx in range(5):
        qz_res = await async_client.post(
            f"/api/v1/projects/{pj_id}/quizzes",
            json={"num_questions": 10, "difficulty_preference": "adaptive"},
            headers=headers,
        )
        assert qz_res.status_code == 201
        questions = qz_res.json()["data"]["questions"]

        for q in questions:
            fp = compute_question_fingerprint(q["question_text"])
            if fp in seen_fingerprints:
                duplicate_count += 1
            seen_fingerprints.add(fp)
            total_questions += 1

    assert total_questions == 50
    assert duplicate_count == 0, f"Found {duplicate_count} duplicate questions across {total_questions} questions!"
