import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError, TenantAccessDeniedError
from app.modules.auth.service import AuthService
from app.modules.knowledge.service import KnowledgeService
from app.modules.mastery.engine import DeterministicMasteryEngine
from app.modules.mastery.models import (
    ConceptMastery,
    ConceptMasteryHistory,
    GrowthSnapshot,
    LearningEvidence,
    MasteryEvent,
)
from app.modules.mastery.schemas import (
    ConceptMasteryHistoryResponse,
    ConceptMasteryResponse,
    GrowthSnapshotResponse,
    GrowthSummaryResponse,
    LearningEvidenceResponse,
    MasteryEventResponse,
    MasteryExplanationResponse,
)
from app.modules.projects.service import ProjectsService

# In-memory storage structures for Mastery & Growth domain fallback
_IN_MEMORY_MASTERY: dict[str, ConceptMastery] = {}
_IN_MEMORY_MASTERY_EVENTS: dict[str, list[MasteryEvent]] = {}
_IN_MEMORY_PROCESSED_EVENT_IDS: set[str] = set()
_IN_MEMORY_GROWTH_SNAPSHOTS: dict[str, list[GrowthSnapshot]] = {}
_IN_MEMORY_LEARNING_EVIDENCE: dict[str, list[LearningEvidence]] = {}
_IN_MEMORY_MASTERY_HISTORY: dict[str, list[ConceptMasteryHistory]] = {}


class MasteryService:
    """Production Concept Mastery and Growth Subsystem Service."""

    def __init__(self, db: AsyncSession | None = None):
        self.db = db
        self.projects_service = ProjectsService(db)
        self.auth_service = AuthService(db)
        self.knowledge_service = KnowledgeService(db)

    async def _authorize(self, user_id: uuid.UUID | str, project_id: uuid.UUID | str) -> None:
        u_id = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        p_id = uuid.UUID(project_id) if isinstance(project_id, str) else project_id
        proj = await self.projects_service.get_project_model(p_id)
        has_access = await self.auth_service.check_space_access(
            user_id=u_id, space_id=proj.space_id, min_role="member"
        )
        if not has_access:
            raise TenantAccessDeniedError("Access denied for project concept mastery subsystem.")

    async def get_concept_mastery_list(
        self, user_id: uuid.UUID, project_id: uuid.UUID
    ) -> list[ConceptMasteryResponse]:
        await self._authorize(user_id, project_id)

        # Ensure project concepts from knowledge base are registered
        concepts_res = await self.knowledge_service.list_project_concepts(user_id=user_id, project_id=project_id)
        concept_names = [c.name for c in concepts_res] if concepts_res else ["General Study Concepts"]

        now = datetime.now(UTC)
        for c_name in concept_names:
            key = f"{project_id}:{user_id}:{c_name}"
            if key not in _IN_MEMORY_MASTERY:
                _IN_MEMORY_MASTERY[key] = ConceptMastery(
                    id=uuid.uuid4(),
                    project_id=project_id,
                    user_id=user_id,
                    concept_id=c_name,
                    mastery_score=0.0,
                    status="stable",
                    last_updated_at=now,
                )

        matched_map: dict[str, ConceptMastery] = {k: v for k, v in _IN_MEMORY_MASTERY.items() if v.project_id == project_id and v.user_id == user_id}

        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(ConceptMastery).where(ConceptMastery.project_id == project_id, ConceptMastery.user_id == user_id)
                res = await self.db.execute(stmt)
                db_m = res.scalars().all()
                for item in db_m:
                    matched_map[item.concept_id] = item
            except Exception:
                await self.db.rollback()

        matched = list(matched_map.values())
        matched.sort(key=lambda x: x.mastery_score, reverse=True)

        return [
            ConceptMasteryResponse(
                id=m.id,
                project_id=m.project_id,
                user_id=m.user_id,
                concept_id=m.concept_id,
                mastery_score=m.mastery_score,
                confidence=getattr(m, "confidence", None) or 0.50,
                status=m.status,  # type: ignore
                last_evaluated_at=getattr(m, "last_evaluated_at", None) or m.last_updated_at,
                last_updated_at=m.last_updated_at,
            )
            for m in matched
        ]

    async def get_single_concept_mastery(
        self, user_id: uuid.UUID, project_id: uuid.UUID, concept_id: str
    ) -> float:
        key = f"{project_id}:{user_id}:{concept_id}"
        m_obj = _IN_MEMORY_MASTERY.get(key)
        if m_obj:
            return m_obj.mastery_score

        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(ConceptMastery).where(
                    ConceptMastery.project_id == project_id,
                    ConceptMastery.user_id == user_id,
                    ConceptMastery.concept_id == concept_id,
                )
                res = await self.db.execute(stmt)
                db_m = res.scalar_one_or_none()
                if db_m:
                    return db_m.mastery_score
            except Exception:
                await self.db.rollback()

        return 0.50

    async def record_mastery_event(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        concept_id: str,
        score_percentage: float,
        difficulty: str = "intermediate",
        event_id: str | None = None,
        event_type: str = "quiz_attempt",
        assessment_id: str | None = None,
    ) -> ConceptMasteryResponse:
        await self._authorize(user_id, project_id)

        # Duplicate event idempotency defense
        if event_id and event_id in _IN_MEMORY_PROCESSED_EVENT_IDS:
            # Return existing mastery record without re-applying delta
            key = f"{project_id}:{user_id}:{concept_id}"
            m = _IN_MEMORY_MASTERY[key]
            return ConceptMasteryResponse(
                id=m.id,
                project_id=m.project_id,
                user_id=m.user_id,
                concept_id=m.concept_id,
                mastery_score=m.mastery_score,
                status=m.status,  # type: ignore
                last_updated_at=m.last_updated_at,
            )

        key = f"{project_id}:{user_id}:{concept_id}"
        now = datetime.now(UTC)

        m_obj = _IN_MEMORY_MASTERY.get(key)
        if not m_obj:
            m_obj = ConceptMastery(
                id=uuid.uuid4(),
                project_id=project_id,
                user_id=user_id,
                concept_id=concept_id,
                mastery_score=0.0,
                status="stable",
                last_updated_at=now,
            )
            _IN_MEMORY_MASTERY[key] = m_obj

        # Count previous mistakes for this concept
        existing_events = _IN_MEMORY_MASTERY_EVENTS.get(str(m_obj.id), [])
        mistakes_count = sum(1 for e in existing_events if e.evidence_json.get("score_percentage", 100.0) < 60.0)

        # Calculate new mastery deterministically
        prev_score = m_obj.mastery_score
        new_score, delta, status, evidence_json = DeterministicMasteryEngine.calculate_new_mastery(
            previous_mastery=prev_score,
            score_percentage=score_percentage,
            difficulty=difficulty,
            repeated_mistakes_count=mistakes_count,
        )

        if assessment_id:
            evidence_json["assessment_id"] = assessment_id

        m_obj.mastery_score = new_score
        m_obj.status = status
        m_obj.confidence = DeterministicMasteryEngine.calculate_confidence(len(existing_events) + 1)
        m_obj.last_evaluated_at = now
        m_obj.last_updated_at = now
        _IN_MEMORY_MASTERY[key] = m_obj

        # 1. Record Learning Evidence
        evidence_rec = LearningEvidence(
            id=uuid.uuid4(),
            user_id=user_id,
            project_id=project_id,
            concept_id=concept_id,
            source_type=event_type,
            source_id=assessment_id or event_id,
            performance=score_percentage / 100.0,
            weight=DeterministicMasteryEngine.SOURCE_WEIGHTS.get(event_type, 1.0),
            evidence_data_json=evidence_json,
            timestamp=now,
        )
        _IN_MEMORY_LEARNING_EVIDENCE.setdefault(str(project_id), []).append(evidence_rec)

        # 2. Record Concept Mastery History Snapshot
        history_rec = ConceptMasteryHistory(
            id=uuid.uuid4(),
            concept_mastery_id=m_obj.id,
            project_id=project_id,
            user_id=user_id,
            concept_id=concept_id,
            mastery_score=new_score,
            confidence=m_obj.confidence,
            status=status,
            evidence_source=event_type,
            recorded_at=now,
        )
        _IN_MEMORY_MASTERY_HISTORY.setdefault(str(project_id), []).append(history_rec)

        # 3. Record Mastery Event log
        evt = MasteryEvent(
            id=uuid.uuid4(),
            mastery_id=m_obj.id,
            user_id=user_id,
            project_id=project_id,
            concept_id=concept_id,
            event_type=event_type,
            previous_mastery=prev_score,
            new_mastery=new_score,
            delta=delta,
            evidence_json=evidence_json,
            timestamp=now,
        )
        _IN_MEMORY_MASTERY_EVENTS.setdefault(str(m_obj.id), []).append(evt)

        if event_id:
            _IN_MEMORY_PROCESSED_EVENT_IDS.add(event_id)

        if self.db is not None:
            try:
                await self.db.merge(m_obj)
                self.db.add(evidence_rec)
                self.db.add(history_rec)
                self.db.add(evt)
                await self.db.commit()
            except Exception:
                await self.db.rollback()

        # Take growth snapshot
        await self._create_growth_snapshot(user_id, project_id)

        return ConceptMasteryResponse(
            id=m_obj.id,
            project_id=m_obj.project_id,
            user_id=m_obj.user_id,
            concept_id=m_obj.concept_id,
            mastery_score=m_obj.mastery_score,
            confidence=m_obj.confidence,
            status=m_obj.status,  # type: ignore
            last_evaluated_at=m_obj.last_evaluated_at,
            last_updated_at=m_obj.last_updated_at,
        )

    async def get_explanation(
        self, user_id: uuid.UUID, project_id: uuid.UUID, concept_id: str
    ) -> MasteryExplanationResponse:
        await self._authorize(user_id, project_id)

        key = f"{project_id}:{user_id}:{concept_id}"
        m_obj = _IN_MEMORY_MASTERY.get(key)
        if not m_obj:
            raise EntityNotFoundError("ConceptMastery", concept_id)

        events = _IN_MEMORY_MASTERY_EVENTS.get(str(m_obj.id), [])
        events.sort(key=lambda x: x.timestamp, reverse=True)

        recent_logs = [
            {
                "event_id": str(e.id),
                "event_type": e.event_type,
                "previous_mastery": e.previous_mastery,
                "new_mastery": e.new_mastery,
                "delta": e.delta,
                "evidence": e.evidence_json,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in events
        ]

        last_delta = events[0].delta if events else 0.0
        prev_m = events[0].previous_mastery if events else 0.0

        return DeterministicMasteryEngine.generate_explanation(
            concept_id=concept_id,
            current_mastery=m_obj.mastery_score,
            previous_mastery=prev_m,
            delta=last_delta,
            status=m_obj.status,
            recent_events=recent_logs,
        )

    async def _create_growth_snapshot(
        self, user_id: uuid.UUID, project_id: uuid.UUID
    ) -> GrowthSnapshot:
        masteries = [
            m for m in _IN_MEMORY_MASTERY.values()
            if m.project_id == project_id and m.user_id == user_id
        ]
        now = datetime.now(UTC)
        if not masteries:
            snap = GrowthSnapshot(
                id=uuid.uuid4(),
                project_id=project_id,
                user_id=user_id,
                snapshot_date=now,
                average_mastery=0.0,
                status_counts={"improving": 0, "stable": 0, "requiring_attention": 0},
                weak_concept_count=0,
                snapshot_data_json={},
                created_at=now,
            )
        else:
            avg_m = round(sum(m.mastery_score for m in masteries) / len(masteries), 4)
            counts = {"improving": 0, "stable": 0, "requiring_attention": 0}
            weak_count = 0
            for m in masteries:
                counts[m.status] = counts.get(m.status, 0) + 1
                if m.mastery_score < 0.60:
                    weak_count += 1

            snap = GrowthSnapshot(
                id=uuid.uuid4(),
                project_id=project_id,
                user_id=user_id,
                snapshot_date=now,
                average_mastery=avg_m,
                status_counts=counts,
                weak_concept_count=weak_count,
                snapshot_data_json={"total_concepts": len(masteries)},
                created_at=now,
            )

        snap_key = f"{project_id}:{user_id}"
        _IN_MEMORY_GROWTH_SNAPSHOTS.setdefault(snap_key, []).append(snap)

        if self.db is not None:
            try:
                self.db.add(snap)
                await self.db.commit()
            except Exception:
                await self.db.rollback()

        return snap

    async def get_growth_summary(
        self, user_id: uuid.UUID, project_id: uuid.UUID
    ) -> GrowthSummaryResponse:
        await self._authorize(user_id, project_id)

        mastery_list = await self.get_concept_mastery_list(user_id, project_id)

        # Check if sufficient data exists (at least 1 recorded mastery event)
        all_event_counts = 0
        for m in mastery_list:
            evs = _IN_MEMORY_MASTERY_EVENTS.get(str(m.id), [])
            all_event_counts += len(evs)

        has_sufficient_data = all_event_counts > 0

        improving = [m for m in mastery_list if m.status == "improving"]
        stable = [m for m in mastery_list if m.status == "stable"]
        req_att = [m for m in mastery_list if m.status == "requiring_attention"]

        overall = (
            round(sum(m.mastery_score for m in mastery_list) / len(mastery_list), 4)
            if mastery_list
            else 0.0
        )

        snap_key = f"{project_id}:{user_id}"
        snaps = _IN_MEMORY_GROWTH_SNAPSHOTS.get(snap_key, [])
        last_snap_at = snaps[-1].created_at if snaps else None

        return GrowthSummaryResponse(
            project_id=project_id,
            user_id=user_id,
            overall_mastery=overall,
            total_concepts=len(mastery_list),
            improving_count=len(improving),
            stable_count=len(stable),
            requiring_attention_count=len(req_att),
            improving_concepts=improving,
            stable_concepts=stable,
            weak_concepts=req_att,
            has_sufficient_data=has_sufficient_data,
            last_snapshot_at=last_snap_at,
        )

    async def get_growth_snapshots(
        self, user_id: uuid.UUID, project_id: uuid.UUID
    ) -> list[GrowthSnapshotResponse]:
        await self._authorize(user_id, project_id)
        snaps: list[GrowthSnapshot] = []

        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(GrowthSnapshot).where(
                    GrowthSnapshot.project_id == project_id, GrowthSnapshot.user_id == user_id
                ).order_by(GrowthSnapshot.snapshot_date)
                res = await self.db.execute(stmt)
                snaps = list(res.scalars().all())
            except Exception:
                pass

        if not snaps:
            snap_key = f"{project_id}:{user_id}"
            snaps = _IN_MEMORY_GROWTH_SNAPSHOTS.get(snap_key, [])
            snaps.sort(key=lambda s: s.snapshot_date)

        return [
            GrowthSnapshotResponse(
                id=s.id,
                project_id=s.project_id,
                user_id=s.user_id,
                snapshot_date=s.snapshot_date,
                average_mastery=s.average_mastery,
                status_counts=s.status_counts,
                weak_concept_count=s.weak_concept_count,
                snapshot_data=s.snapshot_data_json,
            )
            for s in snaps
        ]

    async def get_all_masteries(self) -> list[ConceptMastery]:
        masteries: list[ConceptMastery] = list(_IN_MEMORY_MASTERY.values())
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(ConceptMastery)
                res = await self.db.execute(stmt)
                db_m = list(res.scalars().all())
                if db_m:
                    return db_m
            except Exception:
                pass
        return masteries

    async def get_user_masteries(self, user_id: uuid.UUID) -> list[ConceptMastery]:
        all_m = await self.get_all_masteries()
        return [m for m in all_m if m.user_id == user_id]

