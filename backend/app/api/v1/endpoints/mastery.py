import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.responses import ApiResponse
from app.modules.auth.dependencies import CurrentUser, require_authenticated_user
from app.modules.mastery.schemas import (
    ConceptMasteryResponse,
    GrowthSnapshotResponse,
    GrowthSummaryResponse,
    MasteryExplanationResponse,
)
from app.modules.mastery.service import MasteryService

router = APIRouter(prefix="/projects/{project_id}", tags=["Concept Mastery & Growth Engine"])


class RecordMasteryEventPayload(BaseModel):
    score_percentage: float = Field(..., ge=0.0, le=100.0)
    difficulty: str = Field(default="intermediate")
    event_id: str | None = None
    event_type: str = Field(default="quiz_attempt")
    assessment_id: str | None = None


@router.get(
    "/mastery",
    response_model=ApiResponse[list[ConceptMasteryResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_concept_masteries(
    project_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Lists concept mastery estimations for the project."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = MasteryService(db)
    result = await service.get_concept_mastery_list(user_id=current_user.user_id, project_id=project_id)
    return ApiResponse.ok(data=result, request_id=request_id)


@router.get(
    "/mastery/{concept_id}/explanation",
    response_model=ApiResponse[MasteryExplanationResponse],
    status_code=status.HTTP_200_OK,
)
async def get_mastery_explanation(
    project_id: uuid.UUID,
    concept_id: str,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Retrieves evidence explainability data ('Why did this change?') for a concept."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = MasteryService(db)
    result = await service.get_explanation(
        user_id=current_user.user_id, project_id=project_id, concept_id=concept_id
    )
    return ApiResponse.ok(data=result, request_id=request_id)


@router.post(
    "/mastery/{concept_id}/record",
    response_model=ApiResponse[ConceptMasteryResponse],
    status_code=status.HTTP_200_OK,
)
async def record_mastery_event(
    project_id: uuid.UUID,
    concept_id: str,
    payload: RecordMasteryEventPayload,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Records a new assessment or practice evidence event updating concept mastery deterministically."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = MasteryService(db)
    result = await service.record_mastery_event(
        user_id=current_user.user_id,
        project_id=project_id,
        concept_id=concept_id,
        score_percentage=payload.score_percentage,
        difficulty=payload.difficulty,
        event_id=payload.event_id,
        event_type=payload.event_type,
        assessment_id=payload.assessment_id,
    )
    return ApiResponse.ok(data=result, request_id=request_id)


@router.get(
    "/growth/summary",
    response_model=ApiResponse[GrowthSummaryResponse],
    status_code=status.HTTP_200_OK,
)
async def get_growth_summary(
    project_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Retrieves project growth summary and concept status counts."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = MasteryService(db)
    result = await service.get_growth_summary(user_id=current_user.user_id, project_id=project_id)
    return ApiResponse.ok(data=result, request_id=request_id)


@router.get(
    "/growth/snapshots",
    response_model=ApiResponse[list[GrowthSnapshotResponse]],
    status_code=status.HTTP_200_OK,
)
async def get_growth_snapshots(
    project_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Retrieves historical growth snapshots for trend visualization."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = MasteryService(db)
    result = await service.get_growth_snapshots(user_id=current_user.user_id, project_id=project_id)
    return ApiResponse.ok(data=result, request_id=request_id)
