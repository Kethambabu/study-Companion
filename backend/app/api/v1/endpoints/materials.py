import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.responses import ApiResponse
from app.modules.auth.dependencies import CurrentUser, require_authenticated_user
from app.modules.materials.schemas import (
    MaterialPageResponse,
    MaterialResponse,
    MaterialRetryResponse,
    PaginatedMaterialsResponse,
    PaginatedPagesResponse,
)
from app.modules.materials.service import MaterialsService

router = APIRouter(tags=["Materials"])


@router.post(
    "/projects/{project_id}/materials",
    response_model=ApiResponse[MaterialResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_material(
    project_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
    file: UploadFile = File(...),
):
    """Uploads a PDF material document into target project."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    file_bytes = await file.read()

    service = MaterialsService(db)
    result = await service.upload_material(
        user_id=current_user.user_id,
        project_id=project_id,
        filename=file.filename or "document.pdf",
        file_bytes=file_bytes,
    )
    return ApiResponse.ok(data=result, request_id=request_id)


@router.get(
    "/projects/{project_id}/materials",
    response_model=ApiResponse[PaginatedMaterialsResponse],
    status_code=status.HTTP_200_OK,
)
async def list_project_materials(
    project_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
    search: Annotated[str | None, Query(description="Search filename")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Lists materials within a specific project."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = MaterialsService(db)
    result = await service.list_materials(
        user_id=current_user.user_id,
        project_id=project_id,
        search=search,
        page=page,
        limit=limit,
    )
    return ApiResponse.ok(data=result, request_id=request_id)


@router.get(
    "/materials",
    response_model=ApiResponse[PaginatedMaterialsResponse],
    status_code=status.HTTP_200_OK,
)
async def list_all_materials(
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
    search: Annotated[str | None, Query(description="Search filename")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Lists all materials across accessible projects."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = MaterialsService(db)
    result = await service.list_materials(
        user_id=current_user.user_id,
        project_id=None,
        search=search,
        page=page,
        limit=limit,
    )
    return ApiResponse.ok(data=result, request_id=request_id)


@router.get(
    "/materials/{material_id}",
    response_model=ApiResponse[MaterialResponse],
    status_code=status.HTTP_200_OK,
)
async def get_material(
    material_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Retrieves detailed material record and processing state."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = MaterialsService(db)
    result = await service.get_material(user_id=current_user.user_id, material_id=material_id)
    return ApiResponse.ok(data=result, request_id=request_id)


@router.get(
    "/materials/{material_id}/pages",
    response_model=ApiResponse[PaginatedPagesResponse],
    status_code=status.HTTP_200_OK,
)
async def get_material_pages(
    material_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    """Retrieves extracted page texts and metadata for a material."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = MaterialsService(db)
    result = await service.get_material_pages(
        user_id=current_user.user_id, material_id=material_id, page=page, limit=limit
    )
    return ApiResponse.ok(data=result, request_id=request_id)


@router.post(
    "/materials/{material_id}/retry",
    response_model=ApiResponse[MaterialRetryResponse],
    status_code=status.HTTP_200_OK,
)
async def retry_material_processing(
    material_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Retries processing for a failed or stalled material document."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = MaterialsService(db)
    result = await service.retry_material(user_id=current_user.user_id, material_id=material_id)
    return ApiResponse.ok(data=result, request_id=request_id)
