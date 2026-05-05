from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_confirmation_token
from app.modules.attendance.models import Attendance, AttendanceStatus, ConfirmedBy
from app.modules.convocations.models import Convocation


class AttendanceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_attendance(
        self,
        convocation_id: int,
        player_id: int,
    ) -> Attendance:
        """
        Crea un registro de asistencia con estado PENDING y token único.
        Se llama cuando el admin convoca a un jugador.
        """
        token = generate_confirmation_token()

        attendance = Attendance(
            convocation_id=convocation_id,
            player_id=player_id,
            confirmation_token=token,
            status=AttendanceStatus.PENDING,
            feedback_generated_by_ai=False,
        )
        self.db.add(attendance)
        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance

    async def confirm_via_token(
        self,
        token: str,
        action: str | None = None,
        confirm: bool | None = None,
    ) -> Attendance:
        """
        Confirma o rechaza asistencia via token único (sin login).
        Acepta action='confirm'/'reject' o confirm=True/False (legacy).
        """
        # Normaliza los dos formatos de llamada
        if action is None and confirm is not None:
            action = "confirm" if confirm else "reject"
        if action not in ("confirm", "reject"):
            raise ValueError("Invalid action")

        result = await self.db.execute(
            select(Attendance).where(Attendance.confirmation_token == token)
        )
        attendance = result.scalar_one_or_none()
        if not attendance:
            raise ValueError("Invalid confirmation token")

        convocation_result = await self.db.execute(
            select(Convocation).where(Convocation.id == attendance.convocation_id)
        )
        convocation = convocation_result.scalar_one()
        if not convocation.is_active:
            raise ValueError("Convocation is no longer active")

        now = datetime.now(UTC)
        deadline = convocation.confirmation_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=UTC)
        if now > deadline:
            attendance.status = AttendanceStatus.EXPIRED
            await self.db.commit()
            raise ValueError("Confirmation deadline has passed")

        if action == "confirm":
            attendance.status = AttendanceStatus.CONFIRMED
            attendance.confirmed_by = ConfirmedBy.PLAYER
        else:
            attendance.status = AttendanceStatus.REJECTED
            attendance.confirmed_by = ConfirmedBy.PLAYER

        attendance.confirmed_at = now
        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance

    async def confirm_via_jwt(
        self,
        convocation_id: int,
        player_id: int,
        action: str,
        confirmed_by: ConfirmedBy,
    ) -> Attendance:
        """
        Confirma o rechaza asistencia via login autenticado.
        Usado cuando el jugador/guardian accede con su cuenta.
        """
        result = await self.db.execute(
            select(Attendance).where(
                Attendance.convocation_id == convocation_id,
                Attendance.player_id == player_id,
            )
        )
        attendance = result.scalar_one_or_none()
        if not attendance:
            raise ValueError("Attendance not found")

        # Verifica convocatoria activa
        convocation_result = await self.db.execute(
            select(Convocation).where(Convocation.id == convocation_id)
        )
        convocation = convocation_result.scalar_one()
        if not convocation.is_active:
            raise ValueError("Convocation is no longer active")

        # Verifica deadline
        now = datetime.now(UTC)
        deadline = convocation.confirmation_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=UTC)
        if now > deadline:
            attendance.status = AttendanceStatus.EXPIRED
            await self.db.commit()
            raise ValueError("Confirmation deadline has passed")

        if action == "confirm":
            attendance.status = AttendanceStatus.CONFIRMED
        elif action == "reject":
            attendance.status = AttendanceStatus.REJECTED
        else:
            raise ValueError("Invalid action")

        attendance.confirmed_by = confirmed_by
        attendance.confirmed_at = now
        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance

    async def admin_confirm(
        self,
        convocation_id: int,
        player_id: int,
        organization_id: int,
    ) -> Attendance:
        """El admin confirma manualmente la asistencia de un jugador."""
        from app.modules.training.models import Session

        # Verifica que la convocatoria pertenece a la organización
        convocation_result = await self.db.execute(
            select(Convocation)
            .join(Session, Session.id == Convocation.session_id)
            .where(
                Convocation.id == convocation_id,
                Session.organization_id == organization_id,
            )
        )
        convocation = convocation_result.scalar_one_or_none()
        if not convocation:
            raise ValueError("Convocation not found")

        result = await self.db.execute(
            select(Attendance).where(
                Attendance.convocation_id == convocation_id,
                Attendance.player_id == player_id,
            )
        )
        attendance = result.scalar_one_or_none()
        if not attendance:
            raise ValueError("Attendance not found")

        attendance.status = AttendanceStatus.CONFIRMED
        attendance.confirmed_by = ConfirmedBy.ADMIN
        attendance.confirmed_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance

    async def expire_pending_attendances(
        self,
        convocation_id: int,
    ) -> int:
        """
        Marca como EXPIRED todas las asistencias PENDING cuya convocatoria
        ya pasó de la fecha límite. Ejecutar en un cron job.
        """
        convocation_result = await self.db.execute(
            select(Convocation).where(Convocation.id == convocation_id)
        )
        convocation = convocation_result.scalar_one()

        now = datetime.now(UTC)
        deadline = convocation.confirmation_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=UTC)

        if now <= deadline:
            return 0  # Aún no expiró

        result = await self.db.execute(
            select(Attendance).where(
                Attendance.convocation_id == convocation_id,
                Attendance.status == AttendanceStatus.PENDING,
            )
        )
        expired = list(result.scalars().all())
        for attendance in expired:
            attendance.status = AttendanceStatus.EXPIRED

        await self.db.commit()
        return len(expired)
