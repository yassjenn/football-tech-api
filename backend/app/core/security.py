import secrets
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__truncate_error=False,
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str, role: str, expires_delta: timedelta | None = None
) -> str:
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def generate_confirmation_token() -> str:
    """
    Genera un token único y seguro para confirmación de asistencia.
    Usa secrets.token_urlsafe — criptográficamente seguro y seguro para URLs.
    32 bytes = 43 caracteres base64url, suficientemente largo para evitar colisiones.
    """
    return secrets.token_urlsafe(32)


def create_confirmation_jwt(attendance_id: int, expires_hours: int = 48) -> str:
    """
    Genera un JWT firmado para confirmación de asistencia via enlace de email.
    Incluye el attendance_id para identificar qué asistencia se confirma.
    Expira en 48 horas por defecto — configurable según fecha límite.
    """
    expire = datetime.now(UTC) + timedelta(hours=expires_hours)
    payload = {
        "sub": str(attendance_id),
        "type": "attendance_confirmation",  # distingue este token de los de auth
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_confirmation_jwt(token: str) -> dict:
    """
    Decodifica un JWT de confirmación de asistencia.
    Verifica que el tipo sea correcto para evitar reutilización de tokens de auth.
    Lanza JWTError si el token es inválido o ha expirado.
    """
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    if payload.get("type") != "attendance_confirmation":
        raise JWTError("Invalid token type")
    return payload
