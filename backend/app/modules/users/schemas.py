from pydantic import BaseModel, EmailStr, Field

from app.modules.users.models import UserRole

# ── Request schemas ────────────────────────────────────────────


class RegisterRequest(BaseModel):
    """Schema para registro de Admin o Coach."""

    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=100)
    role: UserRole = UserRole.ADMIN
    organization_name: str | None = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    """Schema para login con email y contraseña."""

    email: EmailStr
    password: str


# ── Response schemas ───────────────────────────────────────────


class TokenResponse(BaseModel):
    """Schema de respuesta con el JWT."""

    access_token: str
    token_type: str = "bearer"
    role: UserRole


class UserResponse(BaseModel):
    """Schema de respuesta con datos del usuario autenticado."""

    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool

    model_config = {"from_attributes": True}
