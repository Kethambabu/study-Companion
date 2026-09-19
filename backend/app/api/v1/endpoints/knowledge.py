import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.responses import ApiResponse
from app.modules.auth.dependencies import CurrentUser, require_authenticated_user
from app.modules.knowledge.schemas import (
    ConceptResponse,
    PaginatedChunksResponse,
    RetrievalSearchResponse,
    SearchQueryRequest,
)
from app.modules.knowledge.service import KnowledgeService

router = APIRouter(prefix="/projects/{project_id}/knowledge", tags=["Knowledge & Retrieval"])


@router.post(
    "/index/{material_id}",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
)
async def index_material(
    project_id: uuid.UUID,
    material_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Indexes processed material pages into project vector chunks and concept graph."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = KnowledgeService(db)
    chunk_count = await service.index_material_knowledge(
        user_id=current_user.user_id, project_id=project_id, material_id=material_id
    )
    return ApiResponse.ok(
        data={"material_id": str(material_id), "chunks_indexed": chunk_count},
        request_id=request_id,
    )


@router.post(
    "/search",
    response_model=ApiResponse[RetrievalSearchResponse],
    status_code=status.HTTP_200_OK,
)
async def search_knowledge(
    project_id: uuid.UUID,
    req: SearchQueryRequest,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Executes full RAG vector retrieval pipeline with reranking and citation evidence."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = KnowledgeService(db)
    result = await service.search_knowledge(
        user_id=current_user.user_id,
        project_id=project_id,
        query=req.query,
        top_k=req.top_k,
        threshold=req.threshold,
        material_id=req.material_id,
    )
    return ApiResponse.ok(data=result, request_id=request_id)


@router.get(
    "/concepts",
    response_model=ApiResponse[list[ConceptResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_concepts(
    project_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Lists concepts extracted for target project."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = KnowledgeService(db)
    concepts = await service.list_project_concepts(
        user_id=current_user.user_id, project_id=project_id
    )
    return ApiResponse.ok(data=concepts, request_id=request_id)


@router.get(
    "/chunks",
    response_model=ApiResponse[PaginatedChunksResponse],
    status_code=status.HTTP_200_OK,
)
async def list_chunks(
    project_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    """Lists indexed vector knowledge chunks for target project."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = KnowledgeService(db)
    result = await service.list_project_chunks(
        user_id=current_user.user_id, project_id=project_id, page=page, limit=limit
    )
    return ApiResponse.ok(data=result, request_id=request_id)
