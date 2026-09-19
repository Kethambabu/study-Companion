from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    space_id: UUID
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    learning_goal: str | None = None


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = None
    learning_goal: str | None = None
    status: str | None = Field(None, pattern="^(active|archived|completed)$")


class ProjectResponse(BaseModel):
    id: UUID
    space_id: UUID
    owner_id: UUID
    name: str
    description: str | None = None
    learning_goal: str | None = None
    status: str = "active"
    materials_count: int = 0
    progress: int = 0
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None


class PaginatedProjectsResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    limit: int
