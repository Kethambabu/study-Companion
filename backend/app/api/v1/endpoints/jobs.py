import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.modules.auth.dependencies import CurrentUser, require_authenticated_user
from app.modules.jobs.runner import BackgroundJobRunner
from app.modules.jobs.schemas import (
    BackgroundJobCreate,
    BackgroundJobResponse,
    JobRetryResponse,
    RecoveryScanResponse,
)

router = APIRouter(prefix="/jobs", tags=["Background Jobs"])


@router.post("", response_model=BackgroundJobResponse, status_code=status.HTTP_201_CREATED)
async def create_background_job(
    req: BackgroundJobCreate,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
):
    """Enqueues an asynchronous background job."""
    user_id = current_user.user_id
    runner = BackgroundJobRunner()
    try:
        return await runner.create_job(user_id=user_id, req=req)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{job_id}", response_model=BackgroundJobResponse)
async def get_job_status(
    job_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
):
    """Queries background job status, progress %, retry counts, and results (PRD 81)."""
    user_id = current_user.user_id
    runner = BackgroundJobRunner()
    try:
        return await runner.get_job(user_id=user_id, job_id=job_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/project/{project_id}", response_model=list[BackgroundJobResponse])
async def list_project_jobs(
    project_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    limit: int = Query(50, ge=1, le=100),
):
    """Lists recent background jobs for a project."""
    user_id = current_user.user_id
    runner = BackgroundJobRunner()
    try:
        return await runner.list_jobs(user_id=user_id, project_id=project_id, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{job_id}/retry", response_model=JobRetryResponse)
async def retry_failed_job(
    job_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
):
    """Manually triggers background job retry with exponential backoff delay (PRD 82)."""
    user_id = current_user.user_id
    runner = BackgroundJobRunner()
    try:
        return await runner.retry_job(user_id=user_id, job_id=job_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/recover-stuck", response_model=RecoveryScanResponse)
async def recover_stuck_jobs(
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    max_processing_time_seconds: int = Query(300, ge=10, le=3600),
):
    """Scans and recovers background jobs stuck in processing state (PRD 84)."""
    runner = BackgroundJobRunner()
    return await runner.recover_stuck_jobs(max_processing_time_seconds=max_processing_time_seconds)

