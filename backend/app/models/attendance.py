from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.convocation import Convocation
    from app.models.player import Player


class AttendanceStatus(enum.StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ConfirmedBy(enum.StrEnum):
    """
    Indica quién realizó la confirmación de asistencia.
    - PLAYER: el jugador confirmó via login o token de email
    - ADMIN: el admin confirmó manualmente desde el dashboard
    """

    PLAYER = "player"
    ADMIN = "admin"


class Attendance(Base, TimestampMixin):
    """
    Registro de asistencia individual de un jugador a una convocatoria.
    La confirmación puede realizarse de tres formas:
    1. Via token único recibido por email (sin login)
    2. Via login del jugador en la plataforma
    3. Via acción manual del admin desde el dashboard
    """

    __tablename__ = "attendances"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    status: Mapped[AttendanceStatus] = mapped_column(
        nullable=False,
        default=AttendanceStatus.PENDING,
    )

    # Token único para confirmación sin login via email
    confirmation_token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Trazabilidad: quién realizó la confirmación
    confirmed_by: Mapped[ConfirmedBy | None] = mapped_column(nullable=True)

    # Evaluaciones post-sesión (RF-21)
    technique_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    physical_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attitude_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_generated_by_ai: Mapped[bool] = mapped_column(
        nullable=False, default=False
    )

    convocation_id: Mapped[int] = mapped_column(
        ForeignKey("convocations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    convocation: Mapped[Convocation] = relationship(back_populates="attendances")
    player: Mapped[Player] = relationship(back_populates="attendances")

    def __repr__(self) -> str:
        return (
            f"<Attendance id={self.id} player_id={self.player_id} status={self.status}>"
        )
