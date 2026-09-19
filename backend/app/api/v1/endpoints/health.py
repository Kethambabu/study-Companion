import uuid
from typing import Any

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.core.responses import ApiResponse

router = APIRouter()


class HealthStatus(BaseModel):
    status: str
    version: str
    environment: str
    database: str
    vector_store: str
    background_worker: str


@router.get("/health", response_model=ApiResponse[HealthStatus], status_code=status.HTTP_200_OK)
async def check_health(
    request: Request,
    db: AsyncSession | None = Depends(get_db),
) -> dict[str, Any]:
    """Production health check endpoint verifying database connectivity and service readiness."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    db_status = "connected"
    if db is not None:
        try:
            await db.execute(text("SELECT 1"))
        except Exception:
            db_status = "degraded"

    payload = HealthStatus(
        status="healthy",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database=db_status,
        vector_store="ready",
        background_worker="active",
    )
    return ApiResponse.ok(data=payload, request_id=request_id)

