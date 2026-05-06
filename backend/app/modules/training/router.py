from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    get_current_admin,
    get_current_admin_or_coach,
    get_current_coach,
)
from app.modules.training.models import SessionStatus
from app.modules.training.schemas import (
    SessionAddContentRequest,
    SessionAssignCoachRequest,
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


@router.post("/{session_id}/assign-coach", response_model=SessionResponse)
async def assign_coach(
    session_id: int,
    data: SessionAssignCoachRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin asigna un entrenador a la sesión.
    La sesión pasa a estado ASSIGNED.
    """
    try:
        service = SessionService(db)
        session = await service.assign_coach(
            session_id, current_user.organization_id, data.coach_id
        )
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/{session_id}/accept", response_model=SessionResponse)
async def accept_session(
    session_id: int,
    current_user: User = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """
    El entrenador acepta la sesión asignada.
    La sesión pasa a estado ACCEPTED.
    """
    try:
        service = SessionService(db)
        coach_profile_id = await service.get_coach_profile_id(
            current_user.id, current_user.organization_id
        )
        session = await service.accept_session(session_id, coach_profile_id)
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/{session_id}/start", response_model=SessionResponse)
async def start_session(
    session_id: int,
    current_user: User = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """
    El entrenador marca la sesión como en curso.
    La sesión pasa a estado IN_PROGRESS.
    """
    try:
        service = SessionService(db)
        coach_profile_id = await service.get_coach_profile_id(
            current_user.id, current_user.organization_id
        )
        session = await service.start_session(session_id, coach_profile_id)
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/{session_id}/complete", response_model=SessionResponse)
async def complete_session(
    session_id: int,
    current_user: User = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """
    El entrenador completa la sesión.
    La sesión pasa a estado COMPLETED.
    """
    try:
        service = SessionService(db)
        coach_profile_id = await service.get_coach_profile_id(
            current_user.id, current_user.organization_id
        )
        session = await service.complete_session(session_id, coach_profile_id)
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.patch("/{session_id}/content", response_model=SessionResponse)
async def add_content(
    session_id: int,
    data: SessionAddContentRequest,
    current_user: User = Depends(get_current_admin_or_coach),
    db: AsyncSession = Depends(get_db),
):
    """
    Añade o actualiza el contenido de ejercicios de la sesión.
    Accesible por admin y coach asignado.
    """
    try:
        service = SessionService(db)
        session = await service.add_content(
            session_id, current_user.organization_id, data.content
        )
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/{session_id}/generate-content", response_model=SessionResponse)
async def generate_content(
    session_id: int,
    current_user: User = Depends(get_current_admin_or_coach),
    db: AsyncSession = Depends(get_db),
):
    """
    Genera contenido de ejercicios para la sesión usando IA.
    El contenido se guarda en la sesión y se marca como generado por IA.
    Accesible por admin y coach.
    """
    try:
        from app.core.ai_content import generate_session_content

        service = SessionService(db)
        session = await service.get_session_by_id(
            session_id, current_user.organization_id
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        if session.status == SessionStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit a completed session",
            )
        if session.status == SessionStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit a cancelled session",
            )

        content = await generate_session_content(
            title=session.title,
            duration_minutes=session.duration_minutes,
            level=session.level,
            age_group=session.age_group,
            description=session.description,
        )

        updated = await service.add_content(
            session_id,
            current_user.organization_id,
            content,
            generated_by_ai=True,
        )
        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e
