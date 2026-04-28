from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.convocations.models import Convocation
    from app.modules.players.models import Player


class AttendanceStatus(enum.StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ConfirmedBy(enum.StrEnum):
    PLAYER = "player"
    GUARDIAN = "guardian"
    ADMIN = "admin"


class Attendance(Base, TimestampMixin):
    __tablename__ = "attendances"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    status: Mapped[AttendanceStatus] = mapped_column(
        nullable=False, default=AttendanceStatus.PENDING
    )
    confirmation_token: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    confirmed_by: Mapped[ConfirmedBy | None] = mapped_column(nullable=True)

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
