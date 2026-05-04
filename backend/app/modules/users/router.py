from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_user
from app.modules.users.models import User
from app.modules.users.schemas import (
    CoachCreateRequest,
    CoachListResponse,
    CoachResponse,
    CoachUpdateRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.modules.users.service import AuthService, CoachService

router = APIRouter(prefix="/auth", tags=["Authentication"])
coach_router = APIRouter(prefix="/coaches", tags=["Coaches"])


# ── Auth endpoints ─────────────────────────────────────────────


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Registra un nuevo usuario. Si el rol es ADMIN crea también la organización."""
    try:
        service = AuthService(db)
        user = await service.register(data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Autentica un usuario y devuelve un JWT."""
    try:
        service = AuthService(db)
        user, token = await service.login(data)
        return TokenResponse(access_token=token, role=user.role)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Devuelve los datos del usuario autenticado."""
    return current_user


# ── Coach endpoints ────────────────────────────────────────────


def _build_coach_response(user: User, coach_profile) -> CoachResponse:
    """Helper para construir la respuesta del entrenador."""
    return CoachResponse(
        id=coach_profile.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        phone=coach_profile.phone,
        bio=coach_profile.bio,
        organization_id=coach_profile.organization_id,
    )


@coach_router.post(
    "", response_model=CoachResponse, status_code=status.HTTP_201_CREATED
)
async def create_coach(
    data: CoachCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Crea un nuevo entrenador en la organización del admin.
    Requiere rol ADMIN.
    """
    try:
        service = CoachService(db)
        user, coach_profile = await service.create_coach(
            data, current_user.organization_id
        )
        return _build_coach_response(user, coach_profile)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@coach_router.get("", response_model=CoachListResponse)
async def list_coaches(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista los entrenadores de la organización con paginación.
    Requiere rol ADMIN.
    """
    service = CoachService(db)
    items, total = await service.get_coaches(
        current_user.organization_id, page, page_size
    )
    return CoachListResponse(
        items=[_build_coach_response(u, cp) for u, cp in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@coach_router.get("/{coach_id}", response_model=CoachResponse)
async def get_coach(
    coach_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Obtiene un entrenador por ID. Requiere rol ADMIN."""
    service = CoachService(db)
    row = await service.get_coach_by_id(coach_id, current_user.organization_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Coach not found"
        )
    user, coach_profile = row
    return _build_coach_response(user, coach_profile)


@coach_router.patch("/{coach_id}", response_model=CoachResponse)
async def update_coach(
    coach_id: int,
    data: CoachUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza datos del entrenador.
    Solo actualiza los campos enviados (PATCH semántico).
    Requiere rol ADMIN.
    """
    try:
        service = CoachService(db)
        user, coach_profile = await service.update_coach(
            coach_id, current_user.organization_id, data
        )
        return _build_coach_response(user, coach_profile)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@coach_router.delete("/{coach_id}", response_model=CoachResponse)
async def deactivate_coach(
    coach_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Desactiva un entrenador (borrado lógico).
    No elimina el registro — preserva historial de sesiones.
    Requiere rol ADMIN.
    """
    try:
        service = CoachService(db)
        user, coach_profile = await service.deactivate_coach(
            coach_id, current_user.organization_id
        )
        return _build_coach_response(user, coach_profile)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
