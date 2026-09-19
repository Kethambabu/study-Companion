from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(None, max_length=255)


class TutorChatRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    mode: str = Field("default", pattern="^(default|explain_simpler|give_example|test_me)$")


class TutorChatResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    answer: str = ""
    content: str = ""
    citations: list[dict] = Field(default_factory=list)
    confidence_status: str = "grounded"
    suggested_followups: list[str] = Field(default_factory=list)
    response_metadata: dict = Field(default_factory=dict)


class ConversationResponse(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationMessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender: str
    content: str
    citations: list[dict] | None = None
    metadata_json: dict | None = None
    created_at: datetime


class PaginatedMessagesResponse(BaseModel):
    items: list[ConversationMessageResponse]
    total: int
    page: int
    limit: int
