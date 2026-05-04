from datetime import date

from pydantic import BaseModel, EmailStr, Field

# ── Player schemas ─────────────────────────────────────────────


class PlayerCreateRequest(BaseModel):
    """Schema para crear un jugador. Solo admin puede usarlo."""

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    birth_date: date | None = None


class PlayerUpdateRequest(BaseModel):
    """Schema para actualizar datos del jugador. Todos los campos opcionales."""

    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    birth_date: date | None = None
    is_active: bool | None = None


class PlayerResponse(BaseModel):
    """Schema de respuesta con datos del jugador."""

    id: int
    email: str
    full_name: str
    is_active: bool
    is_minor: bool
    phone: str | None
    birth_date: date | None
    organization_id: int
    user_id: int | None

    model_config = {"from_attributes": True}


class PlayerListResponse(BaseModel):
    """Schema para listado de jugadores con paginación."""

    items: list[PlayerResponse]
    total: int
    page: int
    page_size: int


# ── Guardian assignment schemas ────────────────────────────────


class GuardianCreateRequest(BaseModel):
    """Schema para crear un guardian y asignarlo a un jugador."""

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    password: str = Field(min_length=8)


class GuardianResponse(BaseModel):
    """Schema de respuesta con datos del guardian."""

    id: int
    email: str
    full_name: str
    is_active: bool
    phone: str | None

    model_config = {"from_attributes": True}


class PlayerGuardianAssignRequest(BaseModel):
    """Schema para asignar un guardian existente a un jugador."""

    guardian_user_id: int
