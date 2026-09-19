from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MaterialResponse(BaseModel):
    id: UUID
    project_id: UUID
    owner_id: UUID
    filename: str
    content_type: str
    storage_path: str
    file_size: int
    checksum: str
    status: str
    progress_pct: int = 0
    current_step: str = "QUEUED"
    error_code: str | None = None
    word_count: int = 0
    estimated_reading_minutes: int = 0
    attempt_count: int = 0
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    page_count: int = 0


class PaginatedMaterialsResponse(BaseModel):
    items: list[MaterialResponse]
    total: int
    page: int
    limit: int


class MaterialPageResponse(BaseModel):
    id: UUID
    material_id: UUID
    page_number: int
    extracted_text: str
    metadata_json: dict | None = None
    created_at: datetime


class PaginatedPagesResponse(BaseModel):
    items: list[MaterialPageResponse]
    total: int
    page: int
    limit: int


class MaterialRetryResponse(BaseModel):
    material_id: UUID
    job_id: UUID
    status: str
    attempt_count: int
