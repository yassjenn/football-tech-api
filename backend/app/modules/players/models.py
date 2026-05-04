from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.attendance.models import Attendance
    from app.modules.organizations.models import Organization
    from app.modules.users.models import GuardianProfile


class Player(Base, TimestampMixin):
    __tablename__ = "players"
    """tabla de jugadores. Cada jugador puede tener un User asociado (si es mayor de edad) y varios GuardianProfiles (si es menor)."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
        index=True,
    )

    organization: Mapped[Organization] = relationship(back_populates="players")
    attendances: Mapped[list[Attendance]] = relationship(back_populates="player")
    guardians: Mapped[list[GuardianProfile]] = relationship(
        secondary="guardian_players",
        back_populates="players",
    )

    @property
    def is_minor(self) -> bool:
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


class GuardianPlayer(Base):
    """Tabla intermedia Guardian ↔ Player."""

    __tablename__ = "guardian_players"

    __table_args__ = (
        UniqueConstraint("guardian_id", "player_id", name="uq_guardian_player"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    guardian_id: Mapped[int] = mapped_column(
        ForeignKey("guardian_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<GuardianPlayer guardian_id={self.guardian_id} player_id={self.player_id}>"
