from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserProfileResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None = None
    role: str = "user"
    is_admin: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse


class SpaceCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    visual_metadata: dict | None = None


class SpaceResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None = None
    visual_metadata: dict | None = None
    owner_id: UUID
    role: str = "owner"
