from __future__ import annotations

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class GuardianPlayer(Base):
    """
    Tabla intermedia entre Guardian y Player.
    Permite la relación muchos a muchos:
    - Un guardian puede tener varios jugadores (hijos)
    - Un jugador puede tener varios guardians (padre y madre)
    La combinación guardian_id + player_id debe ser única.
    """

    __tablename__ = "guardian_players"

    __table_args__ = (
        UniqueConstraint("guardian_id", "player_id", name="uq_guardian_player"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    guardian_id: Mapped[int] = mapped_column(
        ForeignKey("guardians.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<GuardianPlayer guardian_id={self.guardian_id} player_id={self.player_id}>"
