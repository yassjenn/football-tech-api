from datetime import date

from pydantic import BaseModel, Field

from app.modules.training.models import SessionLevel, SessionStatus


class SessionCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = None
    session_date: date
    duration_minutes: int = Field(default=90, ge=30, le=300)
    level: SessionLevel = SessionLevel.INTERMEDIATE
    age_group: str | None = Field(default=None, max_length=20)


class SessionUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    session_date: date | None = None
    duration_minutes: int | None = Field(default=None, ge=30, le=300)
    level: SessionLevel | None = None
    age_group: str | None = None


class SessionResponse(BaseModel):
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


class SessionListResponse(BaseModel):
    items: list[SessionResponse]
    total: int
    page: int
    page_size: int
