from pydantic import BaseModel, EmailStr, Field

from app.modules.users.models import UserRole

# ── Auth schemas ───────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=100)
    role: UserRole = UserRole.ADMIN
    organization_name: str | None = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool

    model_config = {"from_attributes": True}


# ── Coach schemas ──────────────────────────────────────────────


class CoachCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    bio: str | None = None


class CoachUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    bio: str | None = None
    is_active: bool | None = None


class CoachResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    phone: str | None
    bio: str | None
    organization_id: int | None

    model_config = {"from_attributes": True}


class CoachListResponse(BaseModel):
    items: list[CoachResponse]
    total: int
    page: int
    page_size: int
