import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.responses import ApiResponse
from app.modules.auth.dependencies import (
    CurrentUser,
    require_authenticated_user,
    require_space_access,
)
from app.modules.auth.schemas import SpaceCreateRequest, SpaceResponse
from app.modules.auth.service import AuthService
from app.modules.spaces.service import (
    DetailedSpaceResponse,
    PaginatedSpacesResponse,
    SpacesService,
    SpaceUpdateRequest,
)

router = APIRouter(prefix="/spaces", tags=["Spaces"])


@router.get("", response_model=ApiResponse[PaginatedSpacesResponse], status_code=status.HTTP_200_OK)
async def list_spaces(
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
    search: Annotated[str | None, Query(description="Search space name or description")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Lists spaces accessible to the authenticated user with search and pagination."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = SpacesService(db)
    spaces = await service.list_spaces(user_id=current_user.user_id, search=search, page=page, limit=limit)
    return ApiResponse.ok(data=spaces, request_id=request_id)


@router.post("", response_model=ApiResponse[SpaceResponse], status_code=status.HTTP_201_CREATED)
async def create_space(
    req: SpaceCreateRequest,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Creates a new space container and registers user as owner."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = AuthService(db)
    space = await service.create_space(current_user.user_id, req)
    return ApiResponse.ok(data=space, request_id=request_id)


@router.get("/{space_id}", response_model=ApiResponse[DetailedSpaceResponse], status_code=status.HTTP_200_OK)
async def get_space_details(
    space_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_space_access(min_role="member"))],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Protected endpoint returning detailed space metadata."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = SpacesService(db)
    space = await service.get_space(user_id=current_user.user_id, space_id=space_id)
    return ApiResponse.ok(data=space, request_id=request_id)


@router.patch("/{space_id}", response_model=ApiResponse[DetailedSpaceResponse], status_code=status.HTTP_200_OK)
async def update_space(
    space_id: uuid.UUID,
    req: SpaceUpdateRequest,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_space_access(min_role="owner"))],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Updates space settings, description, or visual theme metadata."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = SpacesService(db)
    space = await service.update_space(user_id=current_user.user_id, space_id=space_id, req=req)
    return ApiResponse.ok(data=space, request_id=request_id)


@router.delete("/{space_id}", response_model=ApiResponse[DetailedSpaceResponse], status_code=status.HTTP_200_OK)
async def archive_space(
    space_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_space_access(min_role="owner"))],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Archives a space container. Requires owner role."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = SpacesService(db)
    space = await service.archive_space(user_id=current_user.user_id, space_id=space_id)
    return ApiResponse.ok(data=space, request_id=request_id)
