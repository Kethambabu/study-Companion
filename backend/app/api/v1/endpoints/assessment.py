import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, status

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.responses import ApiResponse
from app.modules.assessment.schemas import (
    QuestionAttemptResponse,
    QuizAttemptResponse,
    QuizCreateRequest,
    QuizResponse,
    QuizSummaryResponse,
    SubmitAnswerRequest,
)
from app.modules.assessment.service import AssessmentService
from app.modules.auth.dependencies import CurrentUser, require_authenticated_user

router = APIRouter(prefix="/projects/{project_id}/quizzes", tags=["Adaptive Assessment"])


@router.post(
    "",
    response_model=ApiResponse[QuizResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_quiz(
    project_id: uuid.UUID,
    req: QuizCreateRequest,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Creates a new project-scoped adaptive assessment quiz session."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = AssessmentService(db)
    result = await service.create_quiz(user_id=current_user.user_id, project_id=project_id, req=req)
    return ApiResponse.ok(data=result, request_id=request_id)


@router.get(
    "",
    response_model=ApiResponse[list[QuizResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_quizzes(
    project_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Lists all quizzes created for the target project."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = AssessmentService(db)
    result = await service.list_quizzes(user_id=current_user.user_id, project_id=project_id)
    return ApiResponse.ok(data=result, request_id=request_id)


@router.post(
    "/{quiz_id}/attempts",
    response_model=ApiResponse[dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
async def start_or_get_attempt(
    project_id: uuid.UUID,
    quiz_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Starts a new quiz attempt or resumes an in-progress session for refresh recovery."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = AssessmentService(db)
    quiz_resp, attempt_resp = await service.start_or_get_attempt(
        user_id=current_user.user_id, project_id=project_id, quiz_id=quiz_id
    )
    return ApiResponse.ok(
        data={"quiz": quiz_resp.model_dump(), "attempt": attempt_resp.model_dump()},
        request_id=request_id,
    )


@router.post(
    "/{quiz_id}/attempts/{attempt_id}/questions/{question_id}/submit",
    response_model=ApiResponse[QuestionAttemptResponse],
    status_code=status.HTTP_200_OK,
)
async def submit_answer(
    project_id: uuid.UUID,
    quiz_id: uuid.UUID,
    attempt_id: uuid.UUID,
    question_id: uuid.UUID,
    req: SubmitAnswerRequest,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Submits answer for a question and returns immediate evaluation feedback without exposing remaining answers."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = AssessmentService(db)
    result = await service.submit_answer(
        user_id=current_user.user_id,
        project_id=project_id,
        quiz_id=quiz_id,
        attempt_id=attempt_id,
        question_id=question_id,
        req=req,
    )
    return ApiResponse.ok(data=result, request_id=request_id)


@router.post(
    "/{quiz_id}/attempts/{attempt_id}/finish",
    response_model=ApiResponse[QuizSummaryResponse],
    status_code=status.HTTP_200_OK,
)
async def finish_attempt(
    project_id: uuid.UUID,
    quiz_id: uuid.UUID,
    attempt_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Finalizes active quiz attempt and returns comprehensive assessment results summary."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = AssessmentService(db)
    result = await service.finish_attempt(
        user_id=current_user.user_id, project_id=project_id, quiz_id=quiz_id, attempt_id=attempt_id
    )
    return ApiResponse.ok(data=result, request_id=request_id)


@router.get(
    "/{quiz_id}/attempts/{attempt_id}/summary",
    response_model=ApiResponse[QuizSummaryResponse],
    status_code=status.HTTP_200_OK,
)
async def get_summary(
    project_id: uuid.UUID,
    quiz_id: uuid.UUID,
    attempt_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Retrieves assessment summary for a completed quiz attempt."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = AssessmentService(db)
    result = await service.get_summary(
        user_id=current_user.user_id, project_id=project_id, quiz_id=quiz_id, attempt_id=attempt_id
    )
    return ApiResponse.ok(data=result, request_id=request_id)


@router.get(
    "/learning-progress",
    response_model=ApiResponse[dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
async def get_learning_progress(
    project_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Retrieves learner's current sequential position and progress through project concepts."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = AssessmentService(db)
    result = await service.get_learning_progress(user_id=current_user.user_id, project_id=project_id)
    return ApiResponse.ok(data=result, request_id=request_id)

