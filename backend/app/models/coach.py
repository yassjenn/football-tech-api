from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Coach(Base, TimestampMixin):
    """
    Perfil de entrenador vinculado a un User.
    Separamos autenticación (User) de datos de dominio (Coach)
    para mantener la tabla users limpia y extensible.
    """

    __tablename__ = "coaches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,  # un user solo puede tener un perfil de coach
        nullable=False,
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relaciones
    user: Mapped["User"] = relationship(back_populates="coach_profile")
    organization: Mapped["Organization"] = relationship()

    def __repr__(self) -> str:
        return f"<Coach id={self.id} user_id={self.user_id}>"
