import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.responses import ApiResponse
from app.modules.auth.dependencies import CurrentUser, require_authenticated_user
from app.modules.auth.schemas import (
    LoginRequest,
    SignupRequest,
    TokenResponse,
    UserProfileResponse,
)
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=ApiResponse[TokenResponse], status_code=status.HTTP_201_CREATED)
async def signup(
    req: SignupRequest,
    request: Request,
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Registers a new user profile and returns access token."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = AuthService(db)
    result = await service.signup(req)
    return ApiResponse.ok(data=result, request_id=request_id)


@router.post("/login", response_model=ApiResponse[TokenResponse], status_code=status.HTTP_200_OK)
async def login(
    req: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Authenticates credentials and returns access token."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = AuthService(db)
    result = await service.login(req)
    return ApiResponse.ok(data=result, request_id=request_id)


@router.post("/logout", response_model=ApiResponse[dict[str, str]], status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
):
    """Logs out user session."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return ApiResponse.ok(data={"message": "Logged out successfully"}, request_id=request_id)


@router.get("/me", response_model=ApiResponse[UserProfileResponse], status_code=status.HTTP_200_OK)
async def get_me(
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    """Retrieves current authenticated user profile."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    service = AuthService(db)
    profile = await service.get_user_profile(current_user.user_id)
    return ApiResponse.ok(data=profile, request_id=request_id)

