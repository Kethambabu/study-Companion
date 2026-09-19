import logging
import uuid
from typing import Any

from app.modules.assessment.service import AssessmentService
from workers.celery_app import celery_app
from workers.utils import run_coro_sync

logger = logging.getLogger("ai_prof.workers.assessment")


@celery_app.task(bind=True, name="assessment.evaluate_quiz", max_retries=3)
def evaluate_quiz_submission_task(
    self,
    user_id_str: str,
    project_id_str: str,
    quiz_id_str: str,
    attempt_id_str: str,
) -> dict[str, Any]:
    """
    Celery background worker task for evaluating open-ended assessment submissions,
    updating concept mastery, and generating explainability snapshots.
    """
    logger.info(f"[Task {self.request.id}] Processing assessment evaluation for attempt_id={attempt_id_str}")

    u_id = uuid.UUID(user_id_str)
    p_id = uuid.UUID(project_id_str)
    q_id = uuid.UUID(quiz_id_str)
    att_id = uuid.UUID(attempt_id_str)

    service = AssessmentService()

    try:
        feedback = run_coro_sync(service.evaluate_quiz_attempt(u_id, q_id, att_id))
        logger.info(f"[Task {self.request.id}] Assessment attempt {attempt_id_str} evaluated successfully. Score: {feedback.score}")
        return {
            "status": "completed",
            "quiz_id": quiz_id_str,
            "attempt_id": attempt_id_str,
            "score": feedback.score,
            "passed": feedback.passed,
        }
    except Exception as exc:
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries
            logger.warning(f"[Task {self.request.id}] Retrying assessment evaluation due to exception: {exc}")
            raise self.retry(exc=exc, countdown=countdown)

        logger.error(f"[Task {self.request.id}] Assessment evaluation failed for attempt_id={attempt_id_str}: {exc}")
        return {
            "status": "failed",
            "attempt_id": attempt_id_str,
            "error": str(exc),
        }
