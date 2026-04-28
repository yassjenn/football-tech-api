from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.organizations.models import Organization
    from app.modules.players.models import Player


class UserRole(enum.StrEnum):
    ADMIN = "admin"
    COACH = "coach"
    GUARDIAN = "guardian"


class User(Base, TimestampMixin):
    """Usuario del sistema con login (Admin, Coach o Guardian)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(nullable=False, default=False)

    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,  # Guardian puede no pertenecer a una org concreta
        index=True,
    )

    organization: Mapped[Organization | None] = relationship(back_populates="users")
    admin_profile: Mapped[AdminProfile | None] = relationship(
        back_populates="user", uselist=False
    )
    coach_profile: Mapped[CoachProfile | None] = relationship(
        back_populates="user", uselist=False
    )
    guardian_profile: Mapped[GuardianProfile | None] = relationship(
        back_populates="user", uselist=False
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"


class AdminProfile(Base, TimestampMixin):
    """Perfil específico del administrador de la organización."""

    __tablename__ = "admin_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user: Mapped[User] = relationship(back_populates="admin_profile")

    def __repr__(self) -> str:
        return f"<AdminProfile id={self.id} user_id={self.user_id}>"


class CoachProfile(Base, TimestampMixin):
    """Perfil específico del entrenador."""

    __tablename__ = "coach_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user: Mapped[User] = relationship(back_populates="coach_profile")

    def __repr__(self) -> str:
        return f"<CoachProfile id={self.id} user_id={self.user_id}>"


class GuardianProfile(Base, TimestampMixin):
    """
    Perfil de padre/tutor. No pertenece a una organización concreta
    pero puede confirmar asistencia de sus hijos en cualquiera.
    """

    __tablename__ = "guardian_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="guardian_profile")
    players: Mapped[list[Player]] = relationship(
        secondary="guardian_players",
        back_populates="guardians",
    )

    def __repr__(self) -> str:
        return f"<GuardianProfile id={self.id} user_id={self.user_id}>"
