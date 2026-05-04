from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_admin_or_coach
from app.modules.training.models import SessionStatus
from app.modules.training.schemas import (
    SessionCreateRequest,
    SessionListResponse,
    SessionResponse,
    SessionUpdateRequest,
)
from app.modules.training.service import SessionService
from app.modules.users.models import User

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Crea una sesión en estado DRAFT. Requiere rol ADMIN."""
    service = SessionService(db)
    session = await service.create_session(data, current_user.organization_id)
    return session


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: SessionStatus | None = Query(default=None),
    current_user: User = Depends(get_current_admin_or_coach),
    db: AsyncSession = Depends(get_db),
):
    """Lista sesiones de la organización. Accesible por Admin y Coach."""
    service = SessionService(db)
    sessions, total = await service.get_sessions(
        current_user.organization_id, page, page_size, status
    )
    return SessionListResponse(
        items=sessions, total=total, page=page, page_size=page_size
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_admin_or_coach),
    db: AsyncSession = Depends(get_db),
):
    """Obtiene una sesión por ID."""
    service = SessionService(db)
    session = await service.get_session_by_id(session_id, current_user.organization_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    return session


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    data: SessionUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza una sesión en estado DRAFT. Requiere rol ADMIN."""
    try:
        service = SessionService(db)
        session = await service.update_session(
            session_id, current_user.organization_id, data
        )
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.delete("/{session_id}", response_model=SessionResponse)
async def cancel_session(
    session_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Cancela una sesión. Requiere rol ADMIN."""
    try:
        service = SessionService(db)
        session = await service.cancel_session(session_id, current_user.organization_id)
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
