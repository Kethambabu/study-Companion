import uuid
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field

ActionTypeLiteral = Literal[
    "review_material",
    "take_quiz",
    "practice_concept",
    "review_mistakes",
    "ask_tutor",
]


class RecommendationResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    action_type: ActionTypeLiteral
    title: str
    description: str
    target_concept_id: str | None = None
    target_resource_id: str | None = None
    priority_score: float = Field(..., ge=0.0, le=1.0)
    status: Literal["active", "completed", "dismissed"]
    reason_evidence: dict[str, Any]
    reason: str = Field(default="", description="Human readable rationale")
    action: str = Field(default="", description="Recommended action instruction")
    concept_id: str | None = Field(default=None, description="Target concept identifier")
    created_at: datetime
    completed_at: datetime | None = None


class NextActionCardResponse(BaseModel):
    recommendation: RecommendationResponse | None = None
    reason: str
    cta_label: str
    cta_path: str
    evidence_summary: list[str] = Field(default_factory=list)
