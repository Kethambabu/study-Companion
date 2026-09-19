import pytest
from httpx import AsyncClient

from app.core.exceptions import LLMGenerationError
from app.modules.assessment.engine import AdaptiveSelectionEngine
from app.modules.assessment.evaluator import QuestionEvaluator
from app.modules.assessment.generator import QuestionGenerator
from app.modules.assessment.schemas import OpenEndedEvaluationSchema


def test_question_generator_valid_schema():
    gen_q = QuestionGenerator.generate_question(
        concept_id="Concurrency",
        difficulty="intermediate",
        question_type="mcq",
        study_context="Concurrency involves thread safety and locks.",
    )
    assert gen_q.question_type == "mcq"
    assert gen_q.concept_id == "Concurrency"
    assert gen_q.difficulty == "intermediate"
    assert len(gen_q.options) == 4
    assert gen_q.correct_answer is not None


def test_invalid_ai_output_rejection():
    invalid_json = '{"question_type": "mcq", "question_text": "Short"}'  # missing required fields
    with pytest.raises(LLMGenerationError):
        QuestionGenerator.generate_question(
            concept_id="Test",
            difficulty="beginner",
            question_type="mcq",
            llm_response_override=invalid_json,
        )


def test_mcq_grading_evaluation():
    is_corr, score, feedback = QuestionEvaluator.evaluate_mcq(
        user_answer="Option A: Correct Choice",
        correct_answer="Option A: Correct Choice",
        explanation="Matches option A.",
    )
    assert is_corr is True
    assert score == 100.0
    assert feedback["is_correct"] is True

    is_corr_wrong, score_wrong, _ = QuestionEvaluator.evaluate_mcq(
        user_answer="Option B: Wrong Choice",
        correct_answer="Option A: Correct Choice",
        explanation="Matches option A.",
    )
    assert is_corr_wrong is False
    assert score_wrong == 0.0


def test_open_ended_evaluation_feedback():
    eval_res: OpenEndedEvaluationSchema = QuestionEvaluator.evaluate_open_ended(
        question_text="Explain raft consensus.",
        user_answer="Raft decomposes consensus into leader election, log replication, and safety guarantees.",
        correct_answer_criteria="Must state leader election, log replication, safety.",
        concept_id="raft_consensus",
    )
    assert eval_res.score_percentage > 50.0
    assert eval_res.is_correct is True
    assert "raft_consensus" in eval_res.key_concepts_demonstrated
    assert len(eval_res.feedback_how_to_improve) > 0


def test_adaptive_selection_engine():
    # 1. Unattempted concept selection
    decision = AdaptiveSelectionEngine.select_adaptive_target(
        history_attempts=[],
        available_concepts=["Raft", "Paxos"],
    )
    assert decision.target_concept_id == "Raft"
    assert decision.target_difficulty == "beginner"

    # 2. Performance escalation to advanced difficulty
    history = [
        {"concept_id": "Raft", "is_correct": True},
        {"concept_id": "Raft", "is_correct": True},
        {"concept_id": "Raft", "is_correct": True},
        {"concept_id": "Raft", "is_correct": True},
        {"concept_id": "Raft", "is_correct": True},
    ]
    decision_adv = AdaptiveSelectionEngine.select_adaptive_target(
        history_attempts=history,
        available_concepts=["Raft"],
    )
    assert decision_adv.target_difficulty == "advanced"


@pytest.mark.asyncio
async def test_quiz_flow_and_duplicate_submission_prevention(async_client: AsyncClient):
    # 1. User signup and space/project setup
    u_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "quiz_user@example.com", "password": "password123"},
    )
    token = u_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    sp = await async_client.post("/api/v1/spaces", json={"name": "Quiz Space", "slug": "quiz-space"}, headers=headers)
    pj = await async_client.post("/api/v1/projects", json={"space_id": sp.json()["data"]["id"], "name": "Quiz Project"}, headers=headers)
    pj_id = pj.json()["data"]["id"]

    # 2. Create Adaptive Quiz
    qz_res = await async_client.post(
        f"/api/v1/projects/{pj_id}/quizzes",
        json={"num_questions": 2, "difficulty_preference": "adaptive"},
        headers=headers,
    )
    assert qz_res.status_code == 201
    qz_data = qz_res.json()["data"]
    qz_id = qz_data["id"]
    questions = qz_data["questions"]
    assert len(questions) == 2

    # Verify correct_answer is NOT exposed in public question response!
    assert "correct_answer" not in questions[0]

    # 3. Start attempt / session recovery
    att_res = await async_client.post(f"/api/v1/projects/{pj_id}/quizzes/{qz_id}/attempts", headers=headers)
    assert att_res.status_code == 200
    att_id = att_res.json()["data"]["attempt"]["id"]

    # 4. Submit Answer for Question 1
    q1_id = questions[0]["id"]
    sub1 = await async_client.post(
        f"/api/v1/projects/{pj_id}/quizzes/{qz_id}/attempts/{att_id}/questions/{q1_id}/submit",
        json={"user_answer": "Option A: The primary mechanism of Core Concepts."},
        headers=headers,
    )
    assert sub1.status_code == 200
    assert "score_percentage" in sub1.json()["data"]

    # 5. Duplicate Submission Defense check (should fail with HTTP 409 Conflict)
    sub1_dup = await async_client.post(
        f"/api/v1/projects/{pj_id}/quizzes/{qz_id}/attempts/{att_id}/questions/{q1_id}/submit",
        json={"user_answer": "Option A: Duplicate click attempt"},
        headers=headers,
    )
    assert sub1_dup.status_code == 409

    # 6. Finish quiz attempt
    fin_res = await async_client.post(
        f"/api/v1/projects/{pj_id}/quizzes/{qz_id}/attempts/{att_id}/finish",
        headers=headers,
    )
    assert fin_res.status_code == 200
    summary = fin_res.json()["data"]
    assert summary["status"] == "completed"
    assert len(summary["recommendations"]) > 0


@pytest.mark.asyncio
async def test_quiz_project_isolation(async_client: AsyncClient):
    # User 1 creates quiz in Project 1
    u1_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "qz_iso1@example.com", "password": "password123"},
    )
    h1 = {"Authorization": f"Bearer {u1_resp.json()['data']['access_token']}"}
    sp1 = await async_client.post("/api/v1/spaces", json={"name": "S1", "slug": "s1-qz"}, headers=h1)
    pj1 = await async_client.post("/api/v1/projects", json={"space_id": sp1.json()["data"]["id"], "name": "P1"}, headers=h1)
    pj1_id = pj1.json()["data"]["id"]

    qz1 = await async_client.post(f"/api/v1/projects/{pj1_id}/quizzes", json={"num_questions": 1}, headers=h1)
    qz1_id = qz1.json()["data"]["id"]

    # User 2 attempts to list/access User 1 quiz -> 403 Access Denied
    u2_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "qz_iso2@example.com", "password": "password123"},
    )
    h2 = {"Authorization": f"Bearer {u2_resp.json()['data']['access_token']}"}

    unauth_res = await async_client.get(f"/api/v1/projects/{pj1_id}/quizzes", headers=h2)
    assert unauth_res.status_code in (403, 404)
