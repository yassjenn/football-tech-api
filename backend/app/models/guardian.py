from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.player import Player


class Guardian(Base, TimestampMixin):
    """
    Padre o tutor legal de uno o más jugadores menores de edad.
    Tiene login propio para acceder a la plataforma, ver las
    convocatorias de sus hijos y confirmar su asistencia.
    Un guardian puede tener varios hijos en la organización
    y un jugador puede tener varios tutores (padre y madre).
    """

    __tablename__ = "guardians"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(nullable=False, default=False)

    # Relación muchos a muchos con Player via tabla intermedia
    players: Mapped[list[Player]] = relationship(
        secondary="guardian_players",
        back_populates="guardians",
    )

    def __repr__(self) -> str:
        return f"<Guardian id={self.id} email={self.email}>"
