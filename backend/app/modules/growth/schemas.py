import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class ConceptStatusSummary(BaseModel):
    concept_id: str
    mastery_score: float
    status: str
    last_updated_at: datetime


class GrowthSummaryResponse(BaseModel):
    project_id: uuid.UUID
    user_id: uuid.UUID
    overall_mastery: float
    mastered_count: int
    improving_count: int
    stable_count: int
    weak_count: int
    total_concepts: int
    improving_concepts: list[ConceptStatusSummary] = Field(default_factory=list)
    stable_concepts: list[ConceptStatusSummary] = Field(default_factory=list)
    weak_concepts: list[ConceptStatusSummary] = Field(default_factory=list)
    generated_at: datetime


class GrowthSnapshotResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    overall_mastery: float
    status_breakdown: dict[str, int]
    snapshot_date: datetime
