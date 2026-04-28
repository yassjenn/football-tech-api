from collections.abc import AsyncGenerator
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import settings


class Base(DeclarativeBase):
    """Clase base para todos los modelos SQLAlchemy."""

    pass


class TimestampMixin:
    """Añade created_at y updated_at a cualquier modelo."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# El engine gestiona el pool de conexiones a PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # muestra las queries SQL en modo debug
    pool_pre_ping=True,  # verifica conexiones antes de usarlas
)

# Factory de sesiones — cada request obtiene su propia sesión
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # evita lazy loading después del commit
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia de FastAPI que provee una sesión de base de datos por request.
    El bloque finally garantiza que la sesión siempre se cierra,
    incluso si hay una excepción.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
