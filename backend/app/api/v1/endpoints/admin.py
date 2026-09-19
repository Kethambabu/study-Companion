import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.admin.schemas import (
    AdminActivityItem,
    AdminDashboardSummaryResponse,
    AdminEngagementAnalyticsResponse,
    AdminLearningAnalyticsResponse,
    AdminOverviewResponse,
    AdminProjectDetailResponse,
    AdminProjectItem,
    AdminSpaceDetailResponse,
    AdminSpaceItem,
    AdminUserItem,
    SystemHealthResponse,
    UserLearningJourneyResponse,
)
from app.modules.admin.service import AdminService
from app.modules.auth.dependencies import CurrentUser, require_admin_user
from app.modules.observability.schemas import (
    AIEvaluationDetailsResponse,
    AIEvaluationMetrics,
    AIObservabilityLogResponse,
    CostSummaryResponse,
    JobLogResponse,
    SingleAIRequestDetailResponse,
    SlowRequestsSummaryResponse,
)
from app.modules.observability.service import ObservabilityService

router = APIRouter(prefix="/admin", tags=["admin"])


# --- 1. Admin Dashboard Summary ---
@router.get("/dashboard/summary", response_model=AdminDashboardSummaryResponse)
async def get_admin_dashboard_summary(
    current_user: Annotated[CurrentUser, Depends(require_admin_user)],
    db: AsyncSession | None = Depends(get_db),
):
    """Admin Feature 1: Real-time aggregated platform summary (GET /admin/dashboard/summary)."""
    service = AdminService(db)
    return await service.get_dashboard_summary(user_id=current_user.user_id)


@router.get("/overview", response_model=AdminOverviewResponse)
async def get_admin_overview(
    current_user: Annotated[CurrentUser, Depends(require_admin_user)],
    db: AsyncSession | None = Depends(get_db),
):
    service = AdminService(db)
    return await service.get_overview(user_id=current_user.user_id)


# --- 2. User Management & Learning Journey Inspection ---
@router.get("/users", response_model=list[AdminUserItem])
async def list_admin_users(
    current_user: Annotated[CurrentUser, Depends(require_admin_user)],
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession | None = Depends(get_db),
):
    """Admin Feature 2: List users with search & role filters."""
    service = AdminService(db)
    return await service.list_users(user_id=current_user.user_id, search=search, limit=limit, offset=offset)


@router.get("/users/{target_user_id}/journey", response_model=UserLearningJourneyResponse)
async def get_student_learning_journey(
    target_user_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(require_admin_user)],
    db: AsyncSession | None = Depends(get_db),
):
    """Admin Feature 2: Deep inspection of a user's learning journey."""
    service = AdminService(db)
    return await service.get_user_journey(user_id=current_user.user_id, target_user_id=target_user_id)


# --- 3. Spaces Overview & Inspection ---
@router.get("/spaces", response_model=list[AdminSpaceItem])
async def list_admin_spaces(
    current_user: Annotated[CurrentUser, Depends(require_admin_user)],
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession | None = Depends(get_db),
):
    """Admin Feature 3: List platform spaces."""
    service = AdminService(db)
    return await service.list_spaces(user_id=current_user.user_id, search=search, limit=limit, offset=offset)


@router.get("/spaces/{space_id}", response_model=AdminSpaceDetailResponse)
async def get_admin_space_detail(
    space_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(require_admin_user)],
    db: AsyncSession | None = Depends(get_db),
):
    """Admin Feature 3: Deep space inspection."""
    service = AdminService(db)
    return await service.get_space_detail(user_id=current_user.user_id, space_id=space_id)


# --- 4. Projects Overview & Inspection ---
@router.get("/projects", response_model=list[AdminProjectItem])
async def list_admin_projects(
    current_user: Annotated[CurrentUser, Depends(require_admin_user)],
    space_id: uuid.UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession | None = Depends(get_db),
):
    """Admin Feature 4: List platform projects across users."""
    service = AdminService(db)
    return await service.list_projects(
        user_id=current_user.user_id, space_id=space_id, search=search, limit=limit, offset=offset
    )


@router.get("/projects/{project_id}", response_model=AdminProjectDetailResponse)
async def get_admin_project_detail(
    project_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(require_admin_user)],
    db: AsyncSession | None = Depends(get_db),
):
    """Admin Feature 4: Deep project inspection."""
    service = AdminService(db)
    return await service.get_project_detail(user_id=current_user.user_id, project_id=project_id)


# --- 5 & 12. Activity Stream & Multi-Filtering ---
@router.get("/activity", response_model=list[AdminActivityItem])
async def list_admin_activity(
    current_user: Annotated[CurrentUser, Depends(require_admin_user)],
    target_user_id: uuid.UUID | None = Query(default=None, alias="user_id"),
    space_id: uuid.UUID | None = Query(default=None),
    project_id: uuid.UUID | None = Query(default=None),
    event_type: str | None = Query(default=None),
    time_range: str | None = Query(default=None),  # today, last_7_days, last_30_days, all
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession | None = Depends(get_db),
):
    """Admin Features 5 & 12: Real-time activity stream with multi-dimensional filtering."""
    service = AdminService(db)
    return await service.list_activity(
        user_id=current_user.user_id,
        target_user_id=target_user_id,
        space_id=space_id,
        project_id=project_id,
        event_type=event_type,
        time_range=time_range,
        limit=limit,
        offset=offset,
    )


# --- 6. Engagement Analytics ---
@router.get("/analytics/engagement", response_model=AdminEngagementAnalyticsResponse)
async def get_admin_engagement_analytics(
    current_user: Annotated[CurrentUser, Depends(require_admin_user)],
    db: AsyncSession | None = Depends(get_db),
):
    """Admin Feature 6: Engagement Analytics (DAU/WAU & activity trends)."""
    service = AdminService(db)
    return await service.get_engagement_analytics(user_id=current_user.user_id)


# --- 7. Learning Analytics ---
@router.get("/analytics/learning", response_model=AdminLearningAnalyticsResponse)
async def get_admin_learning_analytics(
    current_user: Annotated[CurrentUser, Depends(require_admin_user)],
    db: AsyncSession | None = Depends(get_db),
):
    """Admin Feature 7: Platform-wide Learning Analytics & Concept Trends."""
    service = AdminService(db)
    return await service.get_learning_analytics(user_id=current_user.user_id)


# --- 8. AI Usage Telemetry ---
@router.get("/ai-usage", response_model=list[AIObservabilityLogResponse])
async def list_admin_ai_usage(
    current_user: Annotated[CurrentUser, Depends(require_admin_user)],
    provider: str | None = Query(default=None),
    feature: str | None = Query(default=None),
    success: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession | None = Depends(get_db),
):
    """Admin Feature 8: AI Usage & Telemetry Logs."""
    admin_service = AdminService(db)
    await admin_service._require_admin(current_user.user_id)

    obs_service = ObservabilityService(db)
    return await obs_service.list_ai_logs(
        provider=provider, feature=feature, success=success, limit=limit, offset=offset
    )


@router.get("/ai-usage/requests/{request_id}", response_model=SingleAIRequestDetailResponse)
async def get_admin_ai_request_detail(
    request_id: str,
    current_user: Annotated[CurrentUser, Depends(require_admin_user)],
    db: AsyncSession | None = Depends(get_db),
):
    """Admin Feature 8: Single AI Request deep dive investigation."""
    admin_service = AdminService(db)
    await admin_service._require_admin(current_user.user_id)

    obs_service = ObservabilityService(db)
    return await obs_service.get_request_detail(request_id)


@router.get("/ai-usage/slow-requests", response_model=SlowRequestsSummaryResponse)
async def list_admin_slow_ai_requests(
    current_user: Annotated[CurrentUser, Depends(require_admin_user)],
    min_latency_ms: float = Query(default=3000.0, ge=100.0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession | None = Depends(get_db),
):
    """Admin Feature 8: Slow AI Request bottleneck investigation."""
    admin_service = AdminService(db)
    await admin_service._require_admin(current_user.user_id)

    obs_service = ObservabilityService(db)
    return await obs_service.list_slow_requests(min_latency_ms=min_latency_ms, limit=limit)


@router.get("/ai-usage/cost-summary", response_model=CostSummaryResponse)
async def get_admin_ai_cost_summary(
    current_user: Annotated[CurrentUser, Depends(require_admin_user)],
    db: AsyncSession | None = Depends(get_db),
):
    """Admin Feature 8: AI Token & Cost summary dashboard."""
    admin_service = AdminService(db)
    await admin_service._require_admin(current_user.user_id)

    obs_service = ObservabilityService(db)
    return await obs_service.get_cost_summary()


# --- 9. AI Evaluation Metrics ---
@router.get("/ai-evaluation", response_model=AIEvaluationMetrics)
async def get_admin_ai_evaluation(
    current_user: Annotated[CurrentUser, Depends(require_admin_user)],
    db: AsyncSession | None = Depends(get_db),
):
    """Admin Feature 9: AI Evaluation Overview."""
    admin_service = AdminService(db)
    await admin_service._require_admin(current_user.user_id)

    obs_service = ObservabilityService(db)
    return await obs_service.get_ai_evaluation_metrics()


@router.get("/ai-evaluation/details", response_model=AIEvaluationDetailsResponse)
async def get_admin_ai_evaluation_details(
    current_user: Annotated[CurrentUser, Depends(require_admin_user)],
    db: AsyncSession | None = Depends(get_db),
):
    """Admin Feature 9: 4-Tier Model Evaluation Metrics."""
    admin_service = AdminService(db)
    await admin_service._require_admin(current_user.user_id)

    obs_service = ObservabilityService(db)
    return await obs_service.get_ai_evaluation_details()


# --- 10. Background Processing Jobs ---
@router.get("/jobs", response_model=list[JobLogResponse])
async def list_admin_jobs(
    current_user: Annotated[CurrentUser, Depends(require_admin_user)],
    status: str | None = Query(default=None),
    job_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession | None = Depends(get_db),
):
    """Admin Feature 10: Background Processing Jobs Status & Retries."""
    admin_service = AdminService(db)
    await admin_service._require_admin(current_user.user_id)

    obs_service = ObservabilityService(db)
    return await obs_service.list_jobs(
        status=status, job_type=job_type, limit=limit, offset=offset
    )


# --- 11. System Health ---
@router.get("/system-health", response_model=SystemHealthResponse)
async def get_admin_system_health(
    current_user: Annotated[CurrentUser, Depends(require_admin_user)],
    db: AsyncSession | None = Depends(get_db),
):
    """Admin Feature 11: System & Application Component Health Monitoring."""
    service = AdminService(db)
    return await service.get_system_health(user_id=current_user.user_id)
