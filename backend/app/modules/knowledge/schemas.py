from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SearchQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)
    threshold: float = Field(0.05, ge=0.0, le=1.0)
    material_id: UUID | None = None


class CitationResponse(BaseModel):
    citation_id: str
    material_id: UUID
    material_name: str
    page_number: int
    chunk_id: UUID
    excerpt: str


class RetrievalDiagnosticsResponse(BaseModel):
    query: str
    candidate_count: int
    selected_count: int
    similarity_scores: list[float]
    reranking_scores: list[float]
    source_pages: list[int]


class RetrievalSearchResponse(BaseModel):
    context: str
    citations: list[CitationResponse]
    diagnostics: RetrievalDiagnosticsResponse


class ConceptResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    definition: str | None = None
    domain: str | None = None
    created_at: datetime


class ChunkResponse(BaseModel):
    id: UUID
    project_id: UUID
    material_id: UUID
    page_number: int
    chunk_index: int
    section_title: str | None = None
    content: str
    metadata_json: dict | None = None
    created_at: datetime


class PaginatedChunksResponse(BaseModel):
    items: list[ChunkResponse]
    total: int
    page: int
    limit: int
