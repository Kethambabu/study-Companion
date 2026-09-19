import uuid
from typing import Annotated

from fastapi import Depends, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import TenantAccessDeniedError, UnauthorizedAccessError
from app.modules.auth.jwt import decode_access_token
from app.modules.auth.service import AuthService


class CurrentUser(BaseModel):
    user_id: uuid.UUID
    email: str
    role: str = "user"
    is_admin: bool = False


async def require_authenticated_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
) -> CurrentUser:
    """Dependency that extracts Bearer token from HTTP Authorization header and resolves authenticated user identity."""
    if not authorization:
        raise UnauthorizedAccessError("Missing Authorization header.")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedAccessError("Invalid Authorization header format. Expected 'Bearer <token>'.")

    token = parts[1]
    payload = decode_access_token(token)
    user_id_str = payload.get("user_id")
    email = payload.get("email")

    if not user_id_str or not email:
        raise UnauthorizedAccessError("Invalid token payload claims.")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedAccessError("Invalid user ID format in token.")

    from app.modules.admin.service import is_user_admin
    auth_service = AuthService(db)
    try:
        profile = await auth_service.get_user_profile(user_uuid)
        role = profile.role
        is_adm = profile.is_admin
    except Exception:
        role = payload.get("role", "user")
        is_adm = is_user_admin(user_uuid, email=email, role=role)

    return CurrentUser(user_id=user_uuid, email=email, role=role, is_admin=is_adm)


async def require_admin_user(
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)]
) -> CurrentUser:
    """Dependency enforcing that the authenticated user possesses administrative privileges."""
    from app.modules.admin.service import is_user_admin
    if current_user.role == "admin" or current_user.is_admin or is_user_admin(current_user.user_id, email=current_user.email, role=current_user.role):
        return current_user
    raise TenantAccessDeniedError("Access denied: Administrative privileges required.")


def require_space_access(min_role: str = "member"):
    """Factory dependency returning an authorization checker for space access."""
    async def space_checker(
        space_id: uuid.UUID,
        current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
        db: Annotated[AsyncSession | None, Depends(get_db)] = None,
    ) -> CurrentUser:
        service = AuthService(db)
        has_access = await service.check_space_access(
            user_id=current_user.user_id, space_id=space_id, min_role=min_role
        )
        if not has_access:
            raise TenantAccessDeniedError(
                f"User does not have required '{min_role}' access for space '{space_id}'."
            )
        return current_user

    return space_checker


def require_project_access(min_role: str = "member"):
    """Factory dependency returning an authorization checker for project access."""
    async def project_checker(
        project_id: uuid.UUID,
        current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
        db: Annotated[AsyncSession | None, Depends(get_db)] = None,
    ) -> CurrentUser:
        from app.modules.projects.service import ProjectsService
        projects_service = ProjectsService(db)
        project = await projects_service.get_project(project_id)

        auth_service = AuthService(db)
        has_access = await auth_service.check_space_access(
            user_id=current_user.user_id, space_id=project.space_id, min_role=min_role
        )
        if not has_access:
            raise TenantAccessDeniedError(
                f"User does not have access to space '{project.space_id}' for project '{project_id}'."
            )
        return current_user

    return project_checker
