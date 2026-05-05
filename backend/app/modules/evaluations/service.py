from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attendance.models import Attendance, AttendanceStatus
from app.modules.convocations.models import Convocation
from app.modules.evaluations.schemas import EvaluationCreateRequest
from app.modules.training.models import Session, SessionStatus


class EvaluationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate_player(
        self,
        session_id: int,
        player_id: int,
        data: EvaluationCreateRequest,
        coach_profile_id: int,
        generated_by_ai: bool = False,
    ) -> Attendance:  # devuelve la asistencia actualizada con la evaluación registrada
        """
        El entrenador evalúa a un jugador.
        La sesión debe estar IN_PROGRESS o COMPLETED.
        El jugador debe tener asistencia CONFIRMED en la convocatoria.
        """
        # Verifica que la sesión existe y el coach es el asignado
        session_result = await self.db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")
        if session.coach_id != coach_profile_id:
            raise ValueError("You are not assigned to this session")
        if session.status not in (SessionStatus.IN_PROGRESS, SessionStatus.COMPLETED):
            raise ValueError("Session must be IN_PROGRESS or COMPLETED to evaluate")

        # Obtiene la convocatoria de la sesión
        convocation_result = await self.db.execute(
            select(Convocation).where(Convocation.session_id == session_id)
        )
        convocation = convocation_result.scalar_one_or_none()
        if not convocation:
            raise ValueError("No convocation found for this session")

        # Obtiene la asistencia del jugador
        attendance_result = await self.db.execute(
            select(Attendance).where(
                Attendance.convocation_id == convocation.id,
                Attendance.player_id == player_id,
            )
        )
        attendance = attendance_result.scalar_one_or_none()
        if not attendance:
            raise ValueError("Player not found in this session")
        if attendance.status != AttendanceStatus.CONFIRMED:
            raise ValueError("Player attendance is not confirmed")

        # Registra la evaluación
        attendance.technique_score = data.technique_score
        attendance.physical_score = data.physical_score
        attendance.attitude_score = data.attitude_score
        attendance.feedback = data.feedback
        attendance.feedback_generated_by_ai = generated_by_ai

        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance

    async def get_session_evaluations(
        self,
        session_id: int,
        organization_id: int,
    ) -> list[Attendance]:
        """
        Obtiene todas las evaluaciones de una sesión.
        Solo devuelve asistencias que tienen evaluación registrada.
        """
        # Verifica que la sesión pertenece a la organización
        session_result = await self.db.execute(
            select(Session).where(
                Session.id == session_id,
                Session.organization_id == organization_id,
            )
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")

        convocation_result = await self.db.execute(
            select(Convocation).where(Convocation.session_id == session_id)
        )
        convocation = convocation_result.scalar_one_or_none()
        if not convocation:
            return []

        result = await self.db.execute(
            select(Attendance).where(
                Attendance.convocation_id == convocation.id,
                Attendance.technique_score.isnot(None),
            )
        )
        return list(result.scalars().all())

    async def get_player_evaluation(
        self,
        session_id: int,
        player_id: int,
        organization_id: int,
    ) -> Attendance:
        """Obtiene la evaluación de un jugador en una sesión."""
        session_result = await self.db.execute(
            select(Session).where(
                Session.id == session_id,
                Session.organization_id == organization_id,
            )
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")

        convocation_result = await self.db.execute(
            select(Convocation).where(Convocation.session_id == session_id)
        )
        convocation = convocation_result.scalar_one_or_none()
        if not convocation:
            raise ValueError("No convocation found for this session")

        result = await self.db.execute(
            select(Attendance).where(
                Attendance.convocation_id == convocation.id,
                Attendance.player_id == player_id,
            )
        )
        attendance = result.scalar_one_or_none()
        if not attendance:
            raise ValueError("Player not found in this session")
        return attendance
