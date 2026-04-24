from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.attendance import Attendance
    from app.models.organization import Organization


class Player(Base, TimestampMixin):
    """
    Jugador de la organización.
    Tiene acceso a la plataforma para visualizar sus sesiones,
    evaluaciones y confirmar asistencia.
    También puede confirmar via token único recibido por email.
    """

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(nullable=False, default=False)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    organization: Mapped[Organization] = relationship(back_populates="players")
    attendances: Mapped[list[Attendance]] = relationship(back_populates="player")

    def __repr__(self) -> str:
        return f"<Player id={self.id} email={self.email}>"
