import uuid
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field

EventTypeLiteral = Literal[
    "PROJECT_CREATED",
    "MATERIAL_UPLOADED",
    "MATERIAL_READY",
    "TUTOR_MESSAGE",
    "QUIZ_STARTED",
    "QUESTION_ANSWERED",
    "QUIZ_COMPLETED",
    "ASSESSMENT_COMPLETED",
    "MASTERY_UPDATED",
    "RECOMMENDATION_CREATED",
    # Legacy string format support
    "project_created",
    "material_uploaded",
    "material_processed",
    "tutor_interaction",
    "quiz_started",
    "question_answered",
    "quiz_completed",
    "assessment_completed",
    "mastery_updated",
    "recommendation_created",
]


class ActivityEventCreate(BaseModel):
    project_id: uuid.UUID
    space_id: uuid.UUID | None = None
    event_type: str
    entity_type: str | None = None
    entity_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None


class ActivityEventResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    space_id: uuid.UUID | None = None
    project_id: uuid.UUID
    event_type: str
    entity_type: str | None = None
    entity_id: str | None = None
    metadata: dict[str, Any]
    status: Literal["pending", "processed", "failed"]
    idempotency_key: str
    created_at: datetime
    processed_at: datetime | None = None


# Compatibility Aliases
LearningEventCreate = ActivityEventCreate
LearningEventResponse = ActivityEventResponse
