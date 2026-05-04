from datetime import UTC, datetime

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_confirmation_jwt, generate_confirmation_token
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
        confirm: bool,
    ) -> Attendance:
        """
        Confirma o rechaza asistencia via token único del enlace de email.
        Verifica que el token existe, que la convocatoria no ha expirado
        y que la asistencia está en estado PENDING.
        """
        # Busca la asistencia por token
        result = await self.db.execute(
            select(Attendance).where(Attendance.confirmation_token == token)
        )
        attendance = result.scalar_one_or_none()

        if not attendance:
            raise ValueError("Invalid confirmation token")

        if attendance.status != AttendanceStatus.PENDING:
            raise ValueError("Attendance already responded")

        # Verifica que la convocatoria no ha expirado
        conv_result = await self.db.execute(
            select(Convocation).where(Convocation.id == attendance.convocation_id)
        )
        convocation = conv_result.scalar_one_or_none()

        if not convocation:
            raise ValueError("Convocation not found")

        now = datetime.now(UTC)
        if now > convocation.confirmation_deadline.replace(tzinfo=UTC):
            attendance.status = AttendanceStatus.EXPIRED
            await self.db.commit()
            raise ValueError("Confirmation deadline has passed")

        # Actualiza el estado
        attendance.status = (
            AttendanceStatus.CONFIRMED if confirm else AttendanceStatus.REJECTED
        )
        attendance.confirmed_at = now
        attendance.confirmed_by = ConfirmedBy.PLAYER

        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance

    async def confirm_via_jwt(
        self,
        jwt_token: str,
        confirm: bool,
        confirmed_by: ConfirmedBy,
    ) -> Attendance:
        """
        Confirma asistencia via JWT firmado.
        Usado por jugadores y guardians autenticados en la plataforma.
        """
        try:
            payload = decode_confirmation_jwt(jwt_token)
            attendance_id = int(payload["sub"])
        except (JWTError, KeyError, ValueError) as err:
            raise ValueError("Invalid confirmation token") from err

        result = await self.db.execute(
            select(Attendance).where(Attendance.id == attendance_id)
        )
        attendance = result.scalar_one_or_none()

        if not attendance:
            raise ValueError("Attendance not found")

        if attendance.status != AttendanceStatus.PENDING:
            raise ValueError("Attendance already responded")

        attendance.status = (
            AttendanceStatus.CONFIRMED if confirm else AttendanceStatus.REJECTED
        )
        attendance.confirmed_at = datetime.now(UTC)
        attendance.confirmed_by = confirmed_by

        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance

    async def admin_confirm(
        self,
        player_id: int,
        convocation_id: int,
        confirm: bool,
    ) -> Attendance:
        """
        El admin confirma o rechaza asistencia manualmente desde el dashboard.
        No requiere token — el admin tiene acceso directo.
        """
        result = await self.db.execute(
            select(Attendance).where(
                Attendance.player_id == player_id,
                Attendance.convocation_id == convocation_id,
            )
        )
        attendance = result.scalar_one_or_none()

        if not attendance:
            raise ValueError("Attendance record not found")

        attendance.status = (
            AttendanceStatus.CONFIRMED if confirm else AttendanceStatus.REJECTED
        )
        attendance.confirmed_at = datetime.now(UTC)
        attendance.confirmed_by = ConfirmedBy.ADMIN

        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance

    async def expire_pending_attendances(self, convocation_id: int) -> int:
        """
        Marca como EXPIRED todas las asistencias PENDING de una convocatoria.
        Se llama cuando expira el plazo de confirmación.
        Devuelve el número de asistencias expiradas.
        """
        result = await self.db.execute(
            select(Attendance).where(
                Attendance.convocation_id == convocation_id,
                Attendance.status == AttendanceStatus.PENDING,
            )
        )
        pending = result.scalars().all()

        for attendance in pending:
            attendance.status = AttendanceStatus.EXPIRED

        await self.db.commit()
        return len(pending)
