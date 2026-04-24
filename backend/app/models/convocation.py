from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.attendance import Attendance
    from app.models.session import Session


class Convocation(Base, TimestampMixin):
    """
    Convocatoria asociada a una sesión.
    El admin define la fecha límite de confirmación.
    Agrupa todos los registros de asistencia de los jugadores convocados.
    """

    __tablename__ = "convocations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    confirmation_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        unique=True,  # una sesión solo tiene una convocatoria
        nullable=False,
    )

    # Relaciones
    session: Mapped[Session] = relationship(back_populates="convocation")
    attendances: Mapped[list[Attendance]] = relationship(back_populates="convocation")

    def __repr__(self) -> str:
        return f"<Convocation id={self.id} session_id={self.session_id}>"
