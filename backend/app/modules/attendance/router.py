from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_user
from app.modules.attendance.models import ConfirmedBy
from app.modules.attendance.schemas import (
    AttendanceAdminConfirmRequest,
    AttendanceConfirmRequest,
    AttendanceResponse,
)
from app.modules.attendance.service import AttendanceService
from app.modules.users.models import User

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("/confirm/{token}", response_model=AttendanceResponse)
async def confirm_via_token(
    token: str,
    data: AttendanceConfirmRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Confirma o rechaza asistencia via token único del enlace de email.
    No requiere autenticación — el token es el mecanismo de seguridad.
    """
    try:
        service = AttendanceService(db)
        attendance = await service.confirm_via_token(token, data.confirm)
        return attendance
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/confirm-authenticated", response_model=AttendanceResponse)
async def confirm_authenticated(
    jwt_token: str,
    data: AttendanceConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Confirma asistencia via JWT para jugadores y guardians autenticados.
    Determina automáticamente el confirmed_by según el rol del usuario.
    """
    from app.modules.users.models import UserRole

    confirmed_by = (
        ConfirmedBy.GUARDIAN
        if current_user.role == UserRole.GUARDIAN
        else ConfirmedBy.PLAYER
    )

    try:
        service = AttendanceService(db)
        attendance = await service.confirm_via_jwt(
            jwt_token, data.confirm, confirmed_by
        )
        return attendance
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/admin-confirm", response_model=AttendanceResponse)
async def admin_confirm(
    data: AttendanceAdminConfirmRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    El admin confirma manualmente la asistencia de un jugador desde el dashboard.
    Requiere rol ADMIN.
    """
    try:
        service = AttendanceService(db)
        attendance = await service.admin_confirm(
            data.player_id, data.convocation_id, data.confirm
        )
        return attendance
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
