from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# CryptContext gestiona el hashing de contraseñas
# bcrypt es el algoritmo recomendado — lento por diseño para dificultar ataques
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__truncate_error=False,  # ← añade esto
)


def hash_password(password: str) -> str:
    """Genera el hash bcrypt de una contraseña en texto plano."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que una contraseña en texto plano coincide con su hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str, role: str, expires_delta: timedelta | None = None
) -> str:
    """
    Genera un JWT firmado con el subject (user id) y el rol.
    El token expira según ACCESS_TOKEN_EXPIRE_MINUTES de config.
    """
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": subject,  # subject: identificador único del usuario
        "role": role,  # rol para control de acceso
        "exp": expire,  # expiración
        "iat": datetime.now(UTC),  # issued at
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decodifica y valida un JWT.
    Lanza JWTError si el token es inválido o ha expirado.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
