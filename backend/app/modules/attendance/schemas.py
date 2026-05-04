from datetime import datetime

from pydantic import BaseModel

from app.modules.attendance.models import AttendanceStatus, ConfirmedBy


class AttendanceConfirmRequest(BaseModel):
    """Schema para confirmar o rechazar asistencia via token."""

    confirm: bool  # True = confirmar, False = rechazar


class AttendanceResponse(BaseModel):
    """Schema de respuesta con el estado de la asistencia."""

    id: int
    status: AttendanceStatus
    confirmed_at: datetime | None
    confirmed_by: ConfirmedBy | None
    player_id: int
    convocation_id: int

    model_config = {"from_attributes": True}


class AttendanceAdminConfirmRequest(BaseModel):
    """Schema para que el admin confirme manualmente la asistencia."""

    player_id: int
    convocation_id: int
    confirm: bool
