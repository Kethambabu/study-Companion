import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.responses import ApiResponse
from app.modules.auth.dependencies import CurrentUser, require_authenticated_user
from app.modules.tutor.schemas import (
    ConversationCreateRequest,
    ConversationResponse,
    PaginatedMessagesResponse,
    TutorChatRequest,
    TutorChatResponse,
)
from app.modules.tutor.service import TutorService

router = APIRouter(prefix="/projects/{project_id}/tutor", tags=["AI Tutor"])


@router.post(
    "/conversations",
    response_model=ApiResponse[ConversationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    project_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
    req: ConversationCreateRequest | None = None,
):
    """Creates a new project-isolated AI Tutor chat conversation session."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = TutorService(db)
    title = req.title if req else None
    result = await service.create_conversation(
        user_id=current_user.user_id, project_id=project_id, title=title
    )
    return ApiResponse.ok(data=result, request_id=request_id)


@router.get(
    "/conversations",
    response_model=ApiResponse[list[ConversationResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_conversations(
    project_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Lists conversations for target project."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = TutorService(db)
    result = await service.list_conversations(
        user_id=current_user.user_id, project_id=project_id
    )
    return ApiResponse.ok(data=result, request_id=request_id)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=ApiResponse[PaginatedMessagesResponse],
    status_code=status.HTTP_200_OK,
)
async def get_messages(
    project_id: uuid.UUID,
    conversation_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    """Retrieves conversation history messages."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = TutorService(db)
    result = await service.get_conversation_messages(
        user_id=current_user.user_id,
        project_id=project_id,
        conversation_id=conversation_id,
        page=page,
        limit=limit,
    )
    return ApiResponse.ok(data=result, request_id=request_id)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ApiResponse[TutorChatResponse],
    status_code=status.HTTP_200_OK,
)
async def send_message(
    project_id: uuid.UUID,
    conversation_id: uuid.UUID,
    req: TutorChatRequest,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Sends a chat message to the grounded AI Tutor and receives structured response."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = TutorService(db)
    result = await service.send_message(
        user_id=current_user.user_id,
        project_id=project_id,
        conversation_id=conversation_id,
        content=req.content,
        mode=req.mode,
        request_id=request_id,
    )
    return ApiResponse.ok(data=result, request_id=request_id)


@router.post(
    "/conversations/{conversation_id}/stream",
    status_code=status.HTTP_200_OK,
)
async def stream_message(
    project_id: uuid.UUID,
    conversation_id: uuid.UUID,
    req: TutorChatRequest,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """PRD 131: Server-Sent Events (SSE) token streaming for RAG AI Tutor response."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = TutorService(db)

    return StreamingResponse(
        service.send_message_stream(
            user_id=current_user.user_id,
            project_id=project_id,
            conversation_id=conversation_id,
            content=req.content,
            mode=req.mode,
            request_id=request_id,
        ),
        media_type="text/event-stream",
    )


@router.get(
    "/learning-context",
    response_model=ApiResponse[dict[str, str]],
    status_code=status.HTTP_200_OK,
)
async def get_learning_context(
    project_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Retrieves persistent student learning context used by AI Tutor."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = TutorService(db)
    raw_ctx = await service.get_persistent_learning_context(user_id=current_user.user_id, project_id=project_id)
    return ApiResponse.ok(data={"learning_context": raw_ctx}, request_id=request_id)
