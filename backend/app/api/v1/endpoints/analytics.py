import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.analytics.schemas import (
    FullAnalyticsBundleResponse,
    GlobalAnalyticsResponse,
    ProjectAnalyticsResponse,
    StudentGlobalAnalyticsResponse,
)
from app.modules.analytics.service import AnalyticsService
from app.modules.auth.dependencies import CurrentUser, require_authenticated_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/student/global", response_model=StudentGlobalAnalyticsResponse)
async def get_student_global_analytics(
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: AsyncSession | None = Depends(get_db),
):
    """Retrieves aggregated student-level global analytics across all spaces & projects."""
    service = AnalyticsService(db)
    return await service.get_student_global_analytics(user_id=current_user.user_id)


@router.get("/project/{project_id}", response_model=ProjectAnalyticsResponse)
async def get_project_analytics(
    project_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: AsyncSession | None = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_project_analytics(user_id=current_user.user_id, project_id=project_id)


@router.get("/project/{project_id}/full", response_model=FullAnalyticsBundleResponse)
async def get_full_analytics_bundle(
    project_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: AsyncSession | None = Depends(get_db),
):
    """Retrieves complete 8-dimension analytics bundle (Project, Global, Learning Activity, Assessment Performance, Mastery, Concept Trends, AI Activity, Learning Progress)."""
    service = AnalyticsService(db)
    return await service.get_full_analytics_bundle(user_id=current_user.user_id, project_id=project_id)


@router.get("/global", response_model=GlobalAnalyticsResponse)
async def get_global_analytics(
    db: AsyncSession | None = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_global_analytics()
