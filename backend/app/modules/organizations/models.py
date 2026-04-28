from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.players.models import Player
    from app.modules.users.models import User


class Organization(Base, TimestampMixin):
    """
    Representa una academia o club de fútbol.
    Es el tenant raíz: todos los usuarios y sesiones pertenecen a una organización.
    """

    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    users: Mapped[list[User]] = relationship(back_populates="organization")
    players: Mapped[list[Player]] = relationship(back_populates="organization")

    def __repr__(self) -> str:
        return f"<Organization id={self.id} slug={self.slug}>"
