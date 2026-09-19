import uuid
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


class BackgroundJobCreate(BaseModel):
    project_id: uuid.UUID
    job_type: str  # e.g. OCR_PROCESSING, MATERIAL_CHUNKING, MASTERY_RECALCULATION, RECOMMENDATION_GENERATION
    payload: dict[str, Any] = Field(default_factory=dict)
    max_retries: int = Field(default=3, ge=1, le=10)


class BackgroundJobResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID
    job_type: str
    status: Literal["pending", "processing", "completed", "failed"]
    progress: float
    retry_count: int
    max_retries: int
    error_code: str | None = None
    error_message: str | None = None
    payload: dict[str, Any]
    result: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class JobRetryResponse(BaseModel):
    job_id: uuid.UUID
    status: str
    retry_count: int
    next_attempt_in_seconds: float
    message: str


class RecoveryScanResponse(BaseModel):
    recovered_count: int
    failed_count: int
    details: list[str]
