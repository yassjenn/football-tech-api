from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class Admin(Base, TimestampMixin):
    """
    Perfil de administrador vinculado a un User.
    El admin es el responsable de la organización: crea convocatorias,
    gestiona entrenadores y jugadores, y asigna sesiones.
    Es el rol con más privilegios del sistema.
    """

    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,  # un user solo puede tener un perfil de admin
        nullable=False,
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relaciones
    user: Mapped[User] = relationship(back_populates="admin_profile")
    organization: Mapped[Organization] = relationship()

    def __repr__(self) -> str:
        return f"<Admin id={self.id} user_id={self.user_id}>"
