import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.responses import ApiResponse
from app.modules.auth.dependencies import (
    CurrentUser,
    require_authenticated_user,
    require_project_access,
)
from app.modules.projects.schemas import (
    PaginatedProjectsResponse,
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.modules.projects.service import ProjectsService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ApiResponse[ProjectResponse], status_code=status.HTTP_201_CREATED)
async def create_project(
    req: ProjectCreateRequest,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Creates a new learning project within a target space container."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    # Verify user access to target space
    from app.modules.auth.service import AuthService
    auth_service = AuthService(db)
    has_space_access = await auth_service.check_space_access(
        user_id=current_user.user_id, space_id=req.space_id, min_role="member"
    )
    if not has_space_access:
        from app.core.exceptions import TenantAccessDeniedError
        raise TenantAccessDeniedError(f"User does not have member access to target space '{req.space_id}'.")

    service = ProjectsService(db)
    project = await service.create_project(user_id=current_user.user_id, req=req)
    return ApiResponse.ok(data=project, request_id=request_id)


@router.get("", response_model=ApiResponse[PaginatedProjectsResponse], status_code=status.HTTP_200_OK)
async def list_projects(
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
    space_id: Annotated[uuid.UUID | None, Query(description="Filter by Space ID")] = None,
    status_filter: Annotated[str | None, Query(alias="status", description="Filter by status (active, archived, completed)")] = None,
    search: Annotated[str | None, Query(description="Search term")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Lists projects with optional space filtering, status filter, search, and pagination."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = ProjectsService(db)
    result = await service.list_projects(
        user_id=current_user.user_id,
        space_id=space_id,
        status_filter=status_filter,
        search=search,
        page=page,
        limit=limit,
    )
    return ApiResponse.ok(data=result, request_id=request_id)


@router.get("/{project_id}", response_model=ApiResponse[ProjectResponse], status_code=status.HTTP_200_OK)
async def get_project(
    project_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_project_access(min_role="member"))],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Retrieves project details by project ID."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = ProjectsService(db)
    project = await service.get_project(project_id)
    return ApiResponse.ok(data=project, request_id=request_id)


@router.patch("/{project_id}", response_model=ApiResponse[ProjectResponse], status_code=status.HTTP_200_OK)
async def update_project(
    project_id: uuid.UUID,
    req: ProjectUpdateRequest,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_project_access(min_role="member"))],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Updates project metadata, status, or learning goal."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = ProjectsService(db)
    updated = await service.update_project(user_id=current_user.user_id, project_id=project_id, req=req)
    return ApiResponse.ok(data=updated, request_id=request_id)


@router.delete("/{project_id}", response_model=ApiResponse[ProjectResponse], status_code=status.HTTP_200_OK)
async def archive_project(
    project_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_project_access(min_role="admin"))],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Archives a project (soft delete). Requires admin or owner role."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = ProjectsService(db)
    archived = await service.archive_project(user_id=current_user.user_id, project_id=project_id)
    return ApiResponse.ok(data=archived, request_id=request_id)
