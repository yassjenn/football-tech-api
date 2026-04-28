from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.attendance.models import Attendance
    from app.modules.training.models import Session


class Convocation(Base, TimestampMixin):
    __tablename__ = "convocations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    confirmation_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    session: Mapped[Session] = relationship(back_populates="convocation")
    attendances: Mapped[list[Attendance]] = relationship(back_populates="convocation")

    def __repr__(self) -> str:
        return f"<Convocation id={self.id} session_id={self.session_id}>"
