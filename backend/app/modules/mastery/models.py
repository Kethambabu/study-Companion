import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.modules.knowledge.models import Concept, ConceptRelationship


class ProjectConcept(Base):
    __tablename__ = "project_concepts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class ConceptMastery(Base):
    __tablename__ = "concept_mastery"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    mastery_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.50)  # 0.0 to 1.0 confidence estimate
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="stable")  # improving, stable, requiring_attention
    last_evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        Index("ix_concept_mastery_project_user_concept", "project_id", "user_id", "concept_id", unique=True),
    )


class LearningEvidence(Base):
    __tablename__ = "learning_evidence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # quiz_attempt, open_ended_assessment, repeated_mistake, tutor_interaction, material_reading
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    performance: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 to 1.0
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    evidence_data_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class ConceptMasteryHistory(Base):
    __tablename__ = "concept_mastery_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_mastery_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("concept_mastery.id", ondelete="CASCADE"), nullable=True, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    mastery_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.50)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="stable")
    evidence_source: Mapped[str] = mapped_column(String(100), nullable=False, default="assessment")
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class MasteryEvent(Base):
    __tablename__ = "mastery_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mastery_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concept_mastery.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, default="assessment")  # quiz_attempt, open_ended_attempt, practice
    previous_mastery: Mapped[float] = mapped_column(Float, nullable=False)
    new_mastery: Mapped[float] = mapped_column(Float, nullable=False)
    delta: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class GrowthSnapshot(Base):
    __tablename__ = "growth_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    average_mastery: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status_counts: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False, default=dict)  # {"improving": 2, "stable": 3, "requiring_attention": 1}
    weak_concept_count: Mapped[int] = mapped_column(nullable=False, default=0)
    snapshot_data_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class LearningProgress(Base):
    __tablename__ = "learning_progress"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    current_concept_id: Mapped[str] = mapped_column(String(255), nullable=False, default="Core Concepts")
    current_position: Mapped[int] = mapped_column(nullable=False, default=1)
    completed_concepts: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    learning_status: Mapped[str] = mapped_column(String(50), nullable=False, default="in_progress")
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        Index("ix_learning_progress_project_user", "project_id", "user_id", unique=True),
    )


