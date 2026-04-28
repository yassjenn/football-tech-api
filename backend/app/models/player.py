from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.attendance import Attendance
    from app.models.guardian import Guardian
    from app.models.organization import Organization


class Player(Base, TimestampMixin):
    """
    Jugador de la organización.
    Si es menor de edad (< 18 años calculado desde birth_date),
    la confirmación de asistencia recae en su guardian.
    Puede tener varios guardians (padre y madre).
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
    guardians: Mapped[list[Guardian]] = relationship(
        secondary="guardian_players",
        back_populates="players",
    )

    @property
    def is_minor(self) -> bool:
        """
        Calcula si el jugador es menor de edad en base a birth_date.
        Si no hay fecha de nacimiento registrada, se asume mayor de edad.
        """
        if self.birth_date is None:
            return False
        today = date.today()
        age = (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )
        return age < 18

    def __repr__(self) -> str:
        return f"<Player id={self.id} email={self.email}>"
