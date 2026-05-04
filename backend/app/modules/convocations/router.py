from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.modules.convocations.schemas import (
    AttendanceSummary,
    ConvocationCreateRequest,
    ConvocationDetailResponse,
    ConvocationResponse,
    SessionResponse,
)
from app.modules.convocations.service import ConvocationService
from app.modules.users.models import User

router = APIRouter(prefix="/convocations", tags=["Convocations"])


@router.post(
    "", response_model=ConvocationResponse, status_code=status.HTTP_201_CREATED
)
async def create_convocation(
    data: ConvocationCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Crea una convocatoria para una sesión y convoca jugadores.
    Genera token único de confirmación para cada jugador.
    Requiere rol ADMIN.
    """
    try:
        service = ConvocationService(db)
        convocation, attendances = await service.create_convocation(
            data, current_user.organization_id
        )
        summary = await service._build_summary(convocation)
        return ConvocationResponse(
            id=convocation.id,
            session_id=convocation.session_id,
            confirmation_deadline=convocation.confirmation_deadline,
            is_active=convocation.is_active,
            **summary,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("", response_model=list[ConvocationResponse])
async def list_convocations(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lista convocatorias de la organización. Requiere rol ADMIN."""
    service = ConvocationService(db)
    convocations = await service.get_convocations(current_user.organization_id)
    result = []
    for conv in convocations:
        summary = await service._build_summary(conv)
        result.append(
            ConvocationResponse(
                id=conv.id,
                session_id=conv.session_id,
                confirmation_deadline=conv.confirmation_deadline,
                is_active=conv.is_active,
                **summary,
            )
        )
    return result


@router.get("/{convocation_id}", response_model=ConvocationDetailResponse)
async def get_convocation(
    convocation_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Obtiene detalle de una convocatoria con asistencias. Requiere rol ADMIN."""
    try:
        service = ConvocationService(db)
        convocation = await service.get_convocation_by_id(
            convocation_id, current_user.organization_id
        )
        if not convocation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convocation not found",
            )

        rows = await service.get_convocation_attendances(
            convocation_id, current_user.organization_id
        )

        from app.modules.training.service import SessionService

        session_service = SessionService(db)
        session = await session_service.get_session_by_id(
            convocation.session_id, current_user.organization_id
        )

        attendances = [
            AttendanceSummary(
                attendance_id=att.id,
                player_id=player.id,
                player_name=player.full_name,
                player_email=player.email,
                status=att.status.value,
                confirmed_at=att.confirmed_at,
                confirmed_by=att.confirmed_by.value if att.confirmed_by else None,
            )
            for att, player in rows
        ]

        return ConvocationDetailResponse(
            id=convocation.id,
            session=SessionResponse.model_validate(session),
            confirmation_deadline=convocation.confirmation_deadline,
            is_active=convocation.is_active,
            attendances=attendances,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("/{convocation_id}/confirmed-players")
async def get_confirmed_players(
    convocation_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene jugadores confirmados de una convocatoria.
    Usado por el admin para asignar la sesión al entrenador.
    """
    try:
        service = ConvocationService(db)
        players = await service.get_confirmed_players(
            convocation_id, current_user.organization_id
        )
        return [
            {"id": p.id, "full_name": p.full_name, "email": p.email} for p in players
        ]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{convocation_id}", response_model=ConvocationResponse)
async def cancel_convocation(
    convocation_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Cancela una convocatoria. Requiere rol ADMIN."""
    try:
        service = ConvocationService(db)
        convocation = await service.cancel_convocation(
            convocation_id, current_user.organization_id
        )
        summary = await service._build_summary(convocation)
        return ConvocationResponse(
            id=convocation.id,
            session_id=convocation.session_id,
            confirmation_deadline=convocation.confirmation_deadline,
            is_active=convocation.is_active,
            **summary,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
