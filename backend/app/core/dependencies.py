from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.modules.users.models import User, UserRole
from app.modules.users.service import AuthService

# OAuth2PasswordBearer extrae el token del header Authorization: Bearer <token>
# tokenUrl indica el endpoint de login para la documentación Swagger
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependencia base — extrae y valida el JWT.
    Devuelve el usuario autenticado o lanza 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception from e

    service = AuthService(db)
    user = await service.get_user_by_id(int(user_id))

    if user is None or not user.is_active:
        raise credentials_exception

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependencia que garantiza que el usuario es Admin.
    Lanza 403 si el rol no es ADMIN.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_current_coach(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependencia que garantiza que el usuario es Coach.
    Lanza 403 si el rol no es COACH.
    """
    if current_user.role != UserRole.COACH:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Coach access required",
        )
    return current_user


async def get_current_admin_or_coach(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependencia que permite acceso a Admin y Coach.
    Útil para endpoints compartidos entre ambos roles.
    """
    if current_user.role not in (UserRole.ADMIN, UserRole.COACH):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Coach access required",
        )
    return current_user


async def get_current_player(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependencia que garantiza que el usuario es Player.
    Lanza 403 si el rol no es PLAYER.
    """
    if current_user.role != UserRole.PLAYER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Player access required",
        )
    return current_user


async def get_current_guardian(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependencia que garantiza que el usuario es Guardian.
    Lanza 403 si el rol no es GUARDIAN.
    """
    if current_user.role != UserRole.GUARDIAN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guardian access required",
        )
    return current_user
