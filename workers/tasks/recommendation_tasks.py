import logging
import uuid
from typing import Any

from app.modules.recommendations.service import RecommendationService
from workers.celery_app import celery_app
from workers.utils import run_coro_sync

logger = logging.getLogger("ai_prof.workers.recommendation")


@celery_app.task(bind=True, name="recommendation.generate", max_retries=3)
def generate_recommendations_task(
    self,
    user_id_str: str,
    project_id_str: str,
) -> dict[str, Any]:
    """
    Celery background worker task for ranking weak concepts and generating
    adaptive Next Action recommendation cards.
    """
    logger.info(f"[Task {self.request.id}] Generating recommendations for project_id={project_id_str}")

    u_id = uuid.UUID(user_id_str)
    p_id = uuid.UUID(project_id_str)

    service = RecommendationService()

    try:
        action_card = run_coro_sync(service.get_next_action_card(u_id, p_id))
        rec_title = action_card.recommendation.title if action_card.recommendation else "Next Study Action"
        logger.info(f"[Task {self.request.id}] Recommendation generated successfully: '{rec_title}'")
        return {
            "status": "completed",
            "project_id": project_id_str,
            "title": rec_title,
            "cta_label": action_card.cta_label,
        }
    except Exception as exc:
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries
            logger.warning(f"[Task {self.request.id}] Retrying recommendation generation due to exception: {exc}")
            raise self.retry(exc=exc, countdown=countdown)

        logger.error(f"[Task {self.request.id}] Recommendation generation failed for project_id={project_id_str}: {exc}")
        return {
            "status": "failed",
            "project_id": project_id_str,
            "error": str(exc),
        }
