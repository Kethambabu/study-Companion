import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AIObservabilityLog(Base):
    """PRD Compliant AI Observability & Telemetry Log Table ('ai_observability_logs') (PRD 85-95)."""
    __tablename__ = "ai_observability_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    request_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    feature: Mapped[str] = mapped_column(String(100), nullable=False, default="tutor")  # tutor, quiz_generation, evaluation, rag, recommendation
    provider: Mapped[str] = mapped_column(String(100), nullable=False)  # groq, gemini, mock, openai
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="grounded", nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Retrieval Evaluation (PRD 92)
    retrieval_relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0 - 1.0
    retrieval_mrr: Mapped[float | None] = mapped_column(Float, nullable=True)  # Mean Reciprocal Rank
    retrieval_precision_at_k: Mapped[float | None] = mapped_column(Float, nullable=True)  # Precision@K
    retrieved_chunk_ids_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    retrieval_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    retrieval_stats_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Tutor Evaluation (PRD 93)
    tutor_groundedness_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0 - 1.0
    tutor_helpfulness_rating: Mapped[float | None] = mapped_column(Float, nullable=True)  # 1.0 - 5.0

    # Assessment Evaluation (PRD 94)
    assessment_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0 - 1.0
    assessment_calibration_error: Mapped[float | None] = mapped_column(Float, nullable=True)  # |Target - Actual|

    # Recommendation Evaluation (PRD 95)
    recommendation_relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0 - 1.0
    recommendation_actionability_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0 - 1.0

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )


class BackgroundJobLog(Base):
    __tablename__ = "background_job_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # queued, processing, completed, failed
    attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
