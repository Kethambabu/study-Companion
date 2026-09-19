import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.responses import ApiResponse
from app.modules.auth.dependencies import CurrentUser, require_authenticated_user
from app.modules.recommendations.schemas import (
    NextActionCardResponse,
    RecommendationResponse,
)
from app.modules.recommendations.service import RecommendationService

router = APIRouter(prefix="/projects/{project_id}/recommendations", tags=["Recommendation Engine"])


@router.get(
    "/next-action",
    response_model=ApiResponse[NextActionCardResponse],
    status_code=status.HTTP_200_OK,
)
async def get_next_action_card(
    project_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Retrieves top recommended Next Action Card for the project."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = RecommendationService(db)
    result = await service.get_next_action_card(user_id=current_user.user_id, project_id=project_id)
    return ApiResponse.ok(data=result, request_id=request_id)


@router.get(
    "",
    response_model=ApiResponse[list[RecommendationResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_recommendations(
    project_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Lists active and historical recommendations for the project."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = RecommendationService(db)
    result = await service.list_recommendations(user_id=current_user.user_id, project_id=project_id)
    return ApiResponse.ok(data=result, request_id=request_id)


@router.post(
    "/{recommendation_id}/complete",
    response_model=ApiResponse[RecommendationResponse],
    status_code=status.HTTP_200_OK,
)
async def complete_recommendation(
    project_id: uuid.UUID,
    recommendation_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Marks a recommendation action as completed by the student."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = RecommendationService(db)
    result = await service.complete_recommendation(
        user_id=current_user.user_id, project_id=project_id, recommendation_id=recommendation_id
    )
    return ApiResponse.ok(data=result, request_id=request_id)


@router.post(
    "/generate",
    response_model=ApiResponse[list[RecommendationResponse]],
    status_code=status.HTTP_200_OK,
)
async def generate_recommendations(
    project_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Triggers the Candidate Generation & Ranking Engine to generate fresh recommendations."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = RecommendationService(db)
    result = await service.generate_recommendations(user_id=current_user.user_id, project_id=project_id)
    return ApiResponse.ok(data=result, request_id=request_id)
