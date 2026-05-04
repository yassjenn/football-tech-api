from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.training.models import SessionLevel, SessionStatus

# ── Session schemas ────────────────────────────────────────────


class SessionCreateRequest(BaseModel):
    """Schema para crear una sesión de entrenamiento."""

    title: str = Field(min_length=2, max_length=200)
    description: str | None = None
    session_date: date
    duration_minutes: int = Field(default=90, ge=30, le=300)
    level: SessionLevel = SessionLevel.INTERMEDIATE
    age_group: str | None = Field(default=None, max_length=20)


class SessionResponse(BaseModel):
    """Schema de respuesta de sesión."""

    id: int
    title: str
    description: str | None
    session_date: date
    duration_minutes: int
    status: SessionStatus
    level: SessionLevel
    age_group: str | None
    content: str | None
    content_generated_by_ai: bool
    organization_id: int
    coach_id: int | None

    model_config = {"from_attributes": True}


# ── Convocation schemas ────────────────────────────────────────


class ConvocationCreateRequest(BaseModel):
    """
    Schema para crear una convocatoria.
    El admin selecciona la sesión, los jugadores y la fecha límite.
    """

    session_id: int
    player_ids: list[int] = Field(min_length=1)
    confirmation_deadline: datetime


class ConvocationResponse(BaseModel):
    """Schema de respuesta de convocatoria."""

    id: int
    session_id: int
    confirmation_deadline: datetime
    is_active: bool
    total_players: int
    confirmed: int
    rejected: int
    pending: int
    expired: int

    model_config = {"from_attributes": True}


class ConvocationDetailResponse(BaseModel):
    """Schema detallado con lista de asistencias."""

    id: int
    session: SessionResponse
    confirmation_deadline: datetime
    is_active: bool
    attendances: list["AttendanceSummary"]

    model_config = {"from_attributes": True}


class AttendanceSummary(BaseModel):
    """Resumen de asistencia de un jugador en una convocatoria."""

    attendance_id: int
    player_id: int
    player_name: str
    player_email: str
    status: str
    confirmed_at: datetime | None
    confirmed_by: str | None
