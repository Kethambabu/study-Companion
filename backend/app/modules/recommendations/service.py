import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError, TenantAccessDeniedError
from app.modules.auth.service import AuthService
from app.modules.materials.service import MaterialsService
from app.modules.mastery.service import MasteryService
from app.modules.projects.service import ProjectsService
from app.modules.recommendations.engine import RecommendationRankingEngine
from app.modules.recommendations.models import Recommendation
from app.modules.recommendations.schemas import (
    NextActionCardResponse,
    RecommendationResponse,
)

# In-memory data store for Recommendations domain fallback
_IN_MEMORY_RECOMMENDATIONS: dict[str, Recommendation] = {}
_IN_MEMORY_REC_KEYS: set[str] = set()


class RecommendationService:
    """Production Recommendation Engine Domain Service."""

    def __init__(self, db: AsyncSession | None = None):
        self.db = db
        self.projects_service = ProjectsService(db)
        self.auth_service = AuthService(db)
        self.mastery_service = MasteryService(db)
        self.materials_service = MaterialsService(db)

    async def _authorize(self, user_id: uuid.UUID | str, project_id: uuid.UUID | str) -> None:
        u_id = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        p_id = uuid.UUID(project_id) if isinstance(project_id, str) else project_id
     
        proj = await self.projects_service.get_project_model(p_id)
        has_access = await self.auth_service.check_space_access(
            user_id=u_id, space_id=proj.space_id, min_role="member"
        )
        if not has_access:
            raise TenantAccessDeniedError("Access denied for project recommendation subsystem.")

    async def generate_recommendations(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        idempotency_key: str | None = None,
    ) -> list[RecommendationResponse]:
        await self._authorize(user_id, project_id)

        key = idempotency_key or f"rec:{project_id}:{user_id}:{uuid.uuid4()}"
        if key in _IN_MEMORY_REC_KEYS:
            return await self.list_recommendations(user_id, project_id)

        _IN_MEMORY_REC_KEYS.add(key)

        # 1. Fetch learner evidence signals
        growth_summary = await self.mastery_service.get_growth_summary(user_id, project_id)
        weak_concept_names = [m.concept_id for m in growth_summary.weak_concepts]
        mastery_list_dto = await self.mastery_service.get_concept_mastery_list(user_id, project_id)
        mastery_dicts = [m.model_dump() for m in mastery_list_dto]

        materials = await self.materials_service.list_materials(user_id=user_id, project_id=project_id)
        materials_count = materials.total if hasattr(materials, "total") else len(getattr(materials, "items", []))

        # 2. Run Candidate Ranking Engine
        candidates = RecommendationRankingEngine.generate_candidate_recommendations(
            weak_concepts=weak_concept_names,
            mastery_list=mastery_dicts,
            recent_mistakes=[],
            materials_count=materials_count,
        )

        now = datetime.now(UTC)
        created_list: list[Recommendation] = []

        # Mark previous active recommendations for this project as dismissed to keep feed fresh
        for rec in _IN_MEMORY_RECOMMENDATIONS.values():
            if rec.project_id == project_id and rec.user_id == user_id and rec.status == "active":
                rec.status = "dismissed"

        for cand in candidates[:3]:  # Top 3 recommendations
            rec_id = uuid.uuid4()
            rec = Recommendation(
                id=rec_id,
                project_id=project_id,
                user_id=user_id,
                action_type=cand["action_type"],
                title=cand["title"],
                description=cand["description"],
                target_concept_id=cand.get("target_concept_id"),
                priority_score=cand["priority_score"],
                status="active",
                reason_evidence_json=cand["reason_evidence"],
                created_at=now,
            )
            _IN_MEMORY_RECOMMENDATIONS[str(rec_id)] = rec
            created_list.append(rec)

        if self.db is not None:
            try:
                for r in created_list:
                    self.db.add(r)
                await self.db.commit()
            except Exception:
                await self.db.rollback()

        return [
            RecommendationResponse(
                id=r.id,
                project_id=r.project_id,
                user_id=r.user_id,
                action_type=r.action_type,  # type: ignore
                title=r.title,
                description=r.description,
                target_concept_id=r.target_concept_id,
                target_resource_id=r.target_resource_id,
                priority_score=r.priority_score,
                status=r.status,  # type: ignore
                reason_evidence=r.reason_evidence_json,
                reason=r.reason,
                action=r.action,
                concept_id=r.concept_id,
                created_at=r.created_at,
                completed_at=r.completed_at,
            )
            for r in created_list
        ]

    async def get_next_action_card(
        self, user_id: uuid.UUID, project_id: uuid.UUID
    ) -> NextActionCardResponse:
        await self._authorize(user_id, project_id)

        active: list[Recommendation] = []
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(Recommendation).where(
                    Recommendation.project_id == project_id,
                    Recommendation.user_id == user_id,
                    Recommendation.status == "active"
                )
                res = await self.db.execute(stmt)
                active = list(res.scalars().all())
            except Exception:
                pass

        if not active:
            active = [
                r for r in _IN_MEMORY_RECOMMENDATIONS.values()
                if r.project_id == project_id and r.user_id == user_id and r.status == "active"
            ]

        if not active:
            # Auto-generate if no active recommendation exists
            generated = await self.generate_recommendations(user_id, project_id)
            if generated:
                rec_dto = generated[0]
            else:
                return NextActionCardResponse(
                    recommendation=None,
                    reason="No active study recommendation generated yet.",
                    cta_label="Take Adaptive Quiz",
                    cta_path="/assessment",
                    evidence_summary=["Initial project study session."],
                )
        else:
            active.sort(key=lambda r: r.priority_score, reverse=True)
            top = active[0]
            rec_dto = RecommendationResponse(
                id=top.id,
                project_id=top.project_id,
                user_id=top.user_id,
                action_type=top.action_type,  # type: ignore
                title=top.title,
                description=top.description,
                target_concept_id=top.target_concept_id,
                target_resource_id=top.target_resource_id,
                priority_score=top.priority_score,
                status=top.status,  # type: ignore
                reason_evidence=top.reason_evidence_json,
                reason=top.reason,
                action=top.action,
                concept_id=top.concept_id,
                created_at=top.created_at,
                completed_at=top.completed_at,
            )

        cta_label, cta_path = RecommendationRankingEngine.ACTION_CTA_MAPPING.get(
            rec_dto.action_type, ("Take Action", "/assessment")
        )

        rationale = rec_dto.reason_evidence.get("rationale", "Based on your project study activity.")

        return NextActionCardResponse(
            recommendation=rec_dto,
            reason=rationale,
            cta_label=cta_label,
            cta_path=cta_path,
            evidence_summary=[rationale],
        )

    async def list_recommendations(
        self, user_id: uuid.UUID, project_id: uuid.UUID
    ) -> list[RecommendationResponse]:
        await self._authorize(user_id, project_id)

        matched: list[Recommendation] = []
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(Recommendation).where(
                    Recommendation.project_id == project_id, Recommendation.user_id == user_id
                )
                res = await self.db.execute(stmt)
                matched = list(res.scalars().all())
            except Exception:
                pass

        if not matched:
            matched = [
                r for r in _IN_MEMORY_RECOMMENDATIONS.values()
                if r.project_id == project_id and r.user_id == user_id
            ]

        matched.sort(key=lambda x: (x.status == "active", x.priority_score), reverse=True)

        return [
            RecommendationResponse(
                id=r.id,
                project_id=r.project_id,
                user_id=r.user_id,
                action_type=r.action_type,  # type: ignore
                title=r.title,
                description=r.description,
                target_concept_id=r.target_concept_id,
                target_resource_id=r.target_resource_id,
                priority_score=r.priority_score,
                status=r.status,  # type: ignore
                reason_evidence=r.reason_evidence_json,
                created_at=r.created_at,
                completed_at=r.completed_at,
            )
            for r in matched
        ]

    async def complete_recommendation(
        self, user_id: uuid.UUID, project_id: uuid.UUID, recommendation_id: uuid.UUID
    ) -> RecommendationResponse:
        await self._authorize(user_id, project_id)

        rec = None
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(Recommendation).where(Recommendation.id == recommendation_id)
                res = await self.db.execute(stmt)
                rec = res.scalar_one_or_none()
            except Exception:
                pass

        if not rec:
            rec = _IN_MEMORY_RECOMMENDATIONS.get(str(recommendation_id))

        if not rec or rec.project_id != project_id or rec.user_id != user_id:
            raise EntityNotFoundError("Recommendation", str(recommendation_id))

        now = datetime.now(UTC)
        rec.status = "completed"
        rec.completed_at = now
        _IN_MEMORY_RECOMMENDATIONS[str(recommendation_id)] = rec

        if self.db is not None:
            try:
                await self.db.commit()
            except Exception:
                await self.db.rollback()

        return RecommendationResponse(
            id=rec.id,
            project_id=rec.project_id,
            user_id=rec.user_id,
            action_type=rec.action_type,  # type: ignore
            title=rec.title,
            description=rec.description,
            target_concept_id=rec.target_concept_id,
            target_resource_id=rec.target_resource_id,
            priority_score=rec.priority_score,
            status=rec.status,  # type: ignore
            reason_evidence=rec.reason_evidence_json,
            created_at=rec.created_at,
            completed_at=rec.completed_at,
        )
