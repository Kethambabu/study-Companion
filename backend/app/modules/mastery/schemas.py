import uuid
from datetime import UTC, datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


class MasteryConfigRequest(BaseModel):
    alpha_recency: float = Field(default=0.3, ge=0.05, le=0.95, description="Recency weighting factor for exponential smoothing")
    mistake_penalty: float = Field(default=0.1, ge=0.0, le=0.5, description="Penalty deducted for repeated mistakes")
    improvement_threshold: float = Field(default=0.03, ge=0.01, description="Delta threshold for classifying status as improving")


class ConceptMasteryResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    concept_id: str
    mastery_score: float = Field(..., ge=0.0, le=1.0, description="Normalized mastery score between 0.0 and 1.0")
    confidence: float = Field(default=0.50, ge=0.0, le=1.0, description="Confidence estimate based on evidence volume & consistency")
    status: Literal["improving", "stable", "requiring_attention"]
    last_evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_updated_at: datetime


class LearningEvidenceResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID
    concept_id: str
    source_type: str
    source_id: str | None = None
    performance: float
    weight: float
    evidence_data: dict[str, Any]
    timestamp: datetime


class ConceptMasteryHistoryResponse(BaseModel):
    id: uuid.UUID
    concept_mastery_id: uuid.UUID | None = None
    project_id: uuid.UUID
    user_id: uuid.UUID
    concept_id: str
    mastery_score: float
    confidence: float
    status: Literal["improving", "stable", "requiring_attention"]
    evidence_source: str
    recorded_at: datetime


class MasteryEventResponse(BaseModel):
    id: uuid.UUID
    mastery_id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID
    concept_id: str
    event_type: str
    previous_mastery: float
    new_mastery: float
    delta: float
    evidence: dict[str, Any]
    timestamp: datetime


class MasteryExplanationResponse(BaseModel):
    concept_id: str
    current_mastery: float
    previous_mastery: float
    delta: float
    status: Literal["improving", "stable", "requiring_attention"]
    explanation: str
    evidence_breakdown: list[dict[str, Any]]
    last_updated_at: datetime


class GrowthSnapshotResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    snapshot_date: datetime
    average_mastery: float
    status_counts: dict[str, int]
    weak_concept_count: int
    snapshot_data: dict[str, Any]


class GrowthSummaryResponse(BaseModel):
    project_id: uuid.UUID
    user_id: uuid.UUID
    overall_mastery: float
    total_concepts: int
    improving_count: int
    stable_count: int
    requiring_attention_count: int
    improving_concepts: list[ConceptMasteryResponse]
    stable_concepts: list[ConceptMasteryResponse]
    weak_concepts: list[ConceptMasteryResponse]
    has_sufficient_data: bool
    last_snapshot_at: datetime | None = None
