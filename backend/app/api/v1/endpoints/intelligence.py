import uuid
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import CurrentUser, require_authenticated_user
from app.modules.intelligence.schemas import LearningIntelligenceSummaryResponse
from app.modules.intelligence.service import LearningIntelligenceService

router = APIRouter(prefix="/projects/{project_id}/intelligence", tags=["intelligence"])


@router.get("", response_model=LearningIntelligenceSummaryResponse)
async def get_project_intelligence(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)] = None,
) -> LearningIntelligenceSummaryResponse:
    service = LearningIntelligenceService(db)
    return await service.get_intelligence_summary(
        user_id=current_user.user_id,
        project_id=project_id,
    )

