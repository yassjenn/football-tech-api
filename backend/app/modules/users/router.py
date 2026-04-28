from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.users.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.modules.users.service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(data: RegisterRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    """
    Registra un nuevo usuario en el sistema.
    Si el rol es ADMIN, crea también la organización.
    """
    try:
        service = AuthService(db)
        user = await service.register(data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    """
    Autentica un usuario y devuelve un JWT.
    El token debe incluirse en el header Authorization: Bearer <token>
    """
    try:
        service = AuthService(db)
        user, token = await service.login(data)
        return TokenResponse(access_token=token, role=user.role)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e
