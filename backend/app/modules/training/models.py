from __future__ import annotations

import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.convocations.models import Convocation
    from app.modules.organizations.models import Organization
    from app.modules.users.models import CoachProfile


class SessionStatus(enum.StrEnum):
    DRAFT = "draft"
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SessionLevel(enum.StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Session(Base, TimestampMixin):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(nullable=False, default=90)
    status: Mapped[SessionStatus] = mapped_column(
        nullable=False, default=SessionStatus.DRAFT
    )
    level: Mapped[SessionLevel] = mapped_column(
        nullable=False, default=SessionLevel.INTERMEDIATE
    )
    age_group: Mapped[str | None] = mapped_column(String(20), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_generated_by_ai: Mapped[bool] = mapped_column(nullable=False, default=False)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    coach_id: Mapped[int | None] = mapped_column(
        ForeignKey("coach_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    organization: Mapped[Organization] = relationship()
    coach: Mapped[CoachProfile | None] = relationship()
    convocation: Mapped[Convocation | None] = relationship(
        back_populates="session", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Session id={self.id} title={self.title} status={self.status}>"
