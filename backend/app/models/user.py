import enum

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    """
    Roles del sistema. Heredar de str permite serializar el enum
    directamente a JSON sin conversión adicional.
    """

    ADMIN = "admin"
    COACH = "coach"


class User(Base, TimestampMixin):
    """
    Usuario del sistema (admin o entrenador).
    Los jugadores no tienen cuenta — confirman asistencia via token único.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relaciones
    organization: Mapped["Organization"] = relationship(back_populates="users")
    coach_profile: Mapped["Coach"] = relationship(back_populates="user", uselist=False)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
