from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.modules.players.schemas import (
    GuardianCreateRequest,
    GuardianResponse,
    PlayerCreateRequest,
    PlayerListResponse,
    PlayerResponse,
    PlayerUpdateRequest,
)
from app.modules.players.service import PlayerService
from app.modules.users.models import User

router = APIRouter(prefix="/players", tags=["Players"])


@router.post("", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
async def create_player(
    data: PlayerCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Crea un jugador en la organización del admin."""
    try:
        service = PlayerService(db)
        player = await service.create_player(data, current_user.organization_id)
        return player
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("", response_model=PlayerListResponse)
async def list_players(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    only_minors: bool | None = Query(default=None),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista jugadores de la organización.
    Permite filtrar por only_minors=true/false.
    """
    service = PlayerService(db)
    players, total = await service.get_players(
        current_user.organization_id, page, page_size, only_minors
    )
    return PlayerListResponse(
        items=players,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(
    player_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Obtiene un jugador por ID."""
    service = PlayerService(db)
    player = await service.get_player_by_id(player_id, current_user.organization_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Player not found"
        )
    return player


@router.patch("/{player_id}", response_model=PlayerResponse)
async def update_player(
    player_id: int,
    data: PlayerUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza datos del jugador."""
    try:
        service = PlayerService(db)
        player = await service.update_player(
            player_id, current_user.organization_id, data
        )
        return player
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{player_id}", response_model=PlayerResponse)
async def deactivate_player(
    player_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Desactiva un jugador (borrado lógico)."""
    try:
        service = PlayerService(db)
        player = await service.deactivate_player(
            player_id, current_user.organization_id
        )
        return player
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/{player_id}/guardians",
    response_model=GuardianResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_guardian(
    player_id: int,
    data: GuardianCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Crea un guardian y lo asigna a un jugador menor.
    Si el guardian ya existe, solo crea la asignación.
    """
    try:
        service = PlayerService(db)
        user, guardian_profile = await service.create_and_assign_guardian(
            player_id, current_user.organization_id, data
        )
        return GuardianResponse(
            id=guardian_profile.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            phone=guardian_profile.phone,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("/{player_id}/guardians", response_model=list[GuardianResponse])
async def get_player_guardians(
    player_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Obtiene los guardians de un jugador."""
    try:
        service = PlayerService(db)
        rows = await service.get_player_guardians(
            player_id, current_user.organization_id
        )
        return [
            GuardianResponse(
                id=gp.id,
                email=u.email,
                full_name=u.full_name,
                is_active=u.is_active,
                phone=gp.phone,
            )
            for u, gp in rows
        ]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
