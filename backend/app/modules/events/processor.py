import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.events.models import ActivityEvent
from app.modules.mastery.service import MasteryService
from app.modules.recommendations.service import RecommendationService

logger = logging.getLogger(__name__)


class EventProcessor:
    """Async event processor for durable activity & learning event pipelines."""

    def __init__(self, db: AsyncSession | None = None):
        self.db = db
        self.mastery_service = MasteryService(db)
        self.recommendation_service = RecommendationService(db)

    async def process_event(self, event: ActivityEvent) -> bool:
        """Processes a single activity event through the background learning workflow pipeline."""
        if event.status == "processed":
            logger.info("Event '%s' already processed (Idempotency check).", event.idempotency_key)
            return True

        try:
            norm_type = event.event_type.upper()

            if norm_type in ("QUIZ_COMPLETED", "QUIZ_COMPLETED"):
                await self._process_quiz_completed(event)
            elif norm_type in ("QUESTION_ANSWERED", "QUESTION_ANSWERED"):
                await self._process_question_answered(event)
            elif norm_type in ("ASSESSMENT_COMPLETED", "ASSESSMENT_COMPLETED"):
                await self._process_assessment_completed(event)
            elif norm_type in ("MATERIAL_READY", "MATERIAL_PROCESSED"):
                await self._process_material_ready(event)
            elif norm_type in ("MASTERY_UPDATED", "MASTERY_UPDATED"):
                await self._process_mastery_updated(event)
            elif norm_type in ("PROJECT_CREATED", "MATERIAL_UPLOADED", "TUTOR_MESSAGE", "QUIZ_STARTED", "RECOMMENDATION_CREATED"):
                logger.info("Activity Event '%s' logged for audit/analytics.", event.event_type)
            else:
                logger.info("Generic Event '%s' recorded.", event.event_type)

            event.status = "processed"
            event.processed_at = datetime.now(UTC)
            return True
        except Exception as err:
            logger.error("Failed to process event '%s': %s", event.idempotency_key, str(err))
            event.status = "failed"
            return False

    async def _process_quiz_completed(self, event: ActivityEvent) -> None:
        meta = event.metadata_json
        user_id = event.user_id
        project_id = event.project_id

        score_pct = meta.get("score_percentage", 100.0)
        weak_concepts = meta.get("weak_concepts", [])

        # 1. Update concept masteries deterministically
        if weak_concepts:
            for c_id in weak_concepts:
                await self.mastery_service.record_mastery_event(
                    user_id=user_id,
                    project_id=project_id,
                    concept_id=str(c_id),
                    score_percentage=score_pct,
                    event_id=f"{event.idempotency_key}:{c_id}",
                    event_type="quiz_completed",
                )

        # 2. Trigger Recommendation Engine to generate fresh Next Action recommendations
        await self.recommendation_service.generate_recommendations(
            user_id=user_id,
            project_id=project_id,
            idempotency_key=f"rec:{event.idempotency_key}",
        )
        logger.info("Processed QUIZ_COMPLETED event for project '%s'.", project_id)

    async def _process_question_answered(self, event: ActivityEvent) -> None:
        meta = event.metadata_json
        user_id = event.user_id
        project_id = event.project_id
        concept_id = meta.get("concept_id")
        is_correct = meta.get("is_correct", False)
        score_pct = 100.0 if is_correct else 0.0

        if concept_id:
            await self.mastery_service.record_mastery_event(
                user_id=user_id,
                project_id=project_id,
                concept_id=str(concept_id),
                score_percentage=score_pct,
                event_id=f"{event.idempotency_key}:{concept_id}",
                event_type="question_answered",
            )
        logger.info("Processed QUESTION_ANSWERED event for concept '%s'.", concept_id)

    async def _process_assessment_completed(self, event: ActivityEvent) -> None:
        meta = event.metadata_json
        user_id = event.user_id
        project_id = event.project_id
        score_pct = meta.get("score_percentage", 80.0)
        concept_id = meta.get("concept_id", "General Assessment")

        await self.mastery_service.record_mastery_event(
            user_id=user_id,
            project_id=project_id,
            concept_id=str(concept_id),
            score_percentage=score_pct,
            event_id=f"{event.idempotency_key}:{concept_id}",
            event_type="open_assessment",
        )

        await self.recommendation_service.generate_recommendations(
            user_id=user_id,
            project_id=project_id,
            idempotency_key=f"rec:assess:{event.idempotency_key}",
        )
        logger.info("Processed ASSESSMENT_COMPLETED event for project '%s'.", project_id)

    async def _process_material_ready(self, event: ActivityEvent) -> None:
        user_id = event.user_id
        project_id = event.project_id

        await self.recommendation_service.generate_recommendations(
            user_id=user_id,
            project_id=project_id,
            idempotency_key=f"rec:mat:{event.idempotency_key}",
        )
        logger.info("Processed MATERIAL_READY event for project '%s'.", project_id)

    async def _process_mastery_updated(self, event: ActivityEvent) -> None:
        user_id = event.user_id
        project_id = event.project_id

        await self.recommendation_service.generate_recommendations(
            user_id=user_id,
            project_id=project_id,
            idempotency_key=f"rec:mast:{event.idempotency_key}",
        )
        logger.info("Processed MASTERY_UPDATED event for project '%s'.", project_id)
