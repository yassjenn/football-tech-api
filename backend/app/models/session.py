from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.coach import Coach
    from app.models.convocation import Convocation
    from app.models.organization import Organization


class SessionStatus(str, enum.Enum):
    """
    Ciclo de vida de una sesión:
    - DRAFT: creada por el admin, pendiente de asignar
    - ASSIGNED: asignada a un entrenador, pendiente de aceptar
    - ACCEPTED: aceptada por el entrenador, en preparación
    - IN_PROGRESS: sesión en curso
    - COMPLETED: sesión finalizada y evaluada
    - CANCELLED: sesión cancelada
    """

    DRAFT = "draft"
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SessionLevel(str, enum.Enum):
    """Nivel de dificultad de la sesión, usado por la IA para generar contenido."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Session(Base, TimestampMixin):
    """
    Sesión de entrenamiento.
    El admin la crea y asigna a un entrenador.
    El entrenador la acepta, prepara y ejecuta.
    """

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_date: Mapped[str] = mapped_column(Date, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(nullable=False, default=90)
    status: Mapped[SessionStatus] = mapped_column(
        nullable=False,
        default=SessionStatus.DRAFT,
    )
    level: Mapped[SessionLevel] = mapped_column(
        nullable=False,
        default=SessionLevel.INTERMEDIATE,
    )
    age_group: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Contenido generado (manual o por IA)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_generated_by_ai: Mapped[bool] = mapped_column(nullable=False, default=False)

    # Claves foráneas
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    coach_id: Mapped[int | None] = mapped_column(
        ForeignKey("coaches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relaciones
    organization: Mapped[Organization] = relationship()
    coach: Mapped[Coach | None] = relationship(back_populates="sessions")
    convocation: Mapped[Convocation | None] = relationship(
        back_populates="session", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Session id={self.id} title={self.title} status={self.status}>"
