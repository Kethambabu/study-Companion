import logging
import uuid
from typing import Any

from app.modules.mastery.service import MasteryService
from workers.celery_app import celery_app
from workers.utils import run_coro_sync

logger = logging.getLogger("ai_prof.workers.mastery")


@celery_app.task(bind=True, name="mastery.update", max_retries=3)
def update_concept_mastery_task(
    self,
    user_id_str: str,
    project_id_str: str,
    concept_id_str: str,
    score_delta: float,
    evidence_type: str,
    idempotency_key: str,
) -> dict[str, Any]:
    """
    Celery background worker task for deterministic concept mastery score calculations,
    idempotent snapshot recording, and explainability tracking.
    """
    logger.info(f"[Task {self.request.id}] Processing concept mastery update for concept={concept_id_str}")

    u_id = uuid.UUID(user_id_str)
    p_id = uuid.UUID(project_id_str)

    service = MasteryService()

    try:
        updated_mastery = run_coro_sync(
            service.record_mastery_event(
                user_id=u_id,
                project_id=p_id,
                concept_id=concept_id_str,
                score_delta=score_delta,
                evidence_type=evidence_type,
                idempotency_key=idempotency_key,
            )
        )
        logger.info(
            f"[Task {self.request.id}] Mastery for concept {concept_id_str} updated to {updated_mastery.mastery_score}"
        )
        return {
            "status": "completed",
            "concept_id": concept_id_str,
            "new_score": float(updated_mastery.mastery_score),
            "status_label": updated_mastery.status,
        }
    except Exception as exc:
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries
            logger.warning(f"[Task {self.request.id}] Retrying mastery update due to exception: {exc}")
            raise self.retry(exc=exc, countdown=countdown)

        logger.error(f"[Task {self.request.id}] Mastery update failed for concept={concept_id_str}: {exc}")
        return {
            "status": "failed",
            "concept_id": concept_id_str,
            "error": str(exc),
        }
