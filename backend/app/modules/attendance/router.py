from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_admin
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
    Confirma o rechaza asistencia via token único (sin login).
    El jugador/guardian clica el enlace del email y llega aquí.
    """
    try:
        service = AttendanceService(db)
        attendance = await service.confirm_via_token(token, data.action)
        return attendance
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/confirm-authenticated", response_model=AttendanceResponse)
async def confirm_via_jwt(
    convocation_id: int,
    player_id: int,
    action: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Confirma o rechaza asistencia cuando el usuario está autenticado.
    Determina automáticamente quién confirma (player/guardian/admin).
    """
    try:
        from app.modules.users.models import UserRole

        if current_user.role == UserRole.ADMIN:
            confirmed_by = ConfirmedBy.ADMIN
        elif current_user.role == UserRole.GUARDIAN:
            confirmed_by = ConfirmedBy.GUARDIAN
        else:
            confirmed_by = ConfirmedBy.PLAYER

        service = AttendanceService(db)
        attendance = await service.confirm_via_jwt(
            convocation_id, player_id, action, confirmed_by
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
    El admin confirma manualmente la asistencia de un jugador.
    Útil cuando el jugador no puede confirmar por su cuenta.
    """
    try:
        service = AttendanceService(db)
        attendance = await service.admin_confirm(
            data.convocation_id, data.player_id, current_user.organization_id
        )
        return attendance
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
