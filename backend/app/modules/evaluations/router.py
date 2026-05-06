from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_admin_or_coach, get_current_coach
from app.modules.evaluations.schemas import EvaluationCreateRequest, EvaluationResponse
from app.modules.evaluations.service import EvaluationService
from app.modules.training.service import SessionService
from app.modules.users.models import User

router = APIRouter(prefix="/sessions", tags=["Evaluations"])


@router.post(
    "/{session_id}/players/{player_id}/evaluate",
    response_model=EvaluationResponse,
)
async def evaluate_player(
    session_id: int,
    player_id: int,
    data: EvaluationCreateRequest,
    current_user: User = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """
    El entrenador evalúa a un jugador de la sesión.
    La sesión debe estar IN_PROGRESS o COMPLETED.
    El jugador debe tener asistencia CONFIRMED.
    """
    try:
        session_service = SessionService(db)
        coach_profile_id = await session_service.get_coach_profile_id(
            current_user.id, current_user.organization_id
        )
        service = EvaluationService(db)
        attendance = await service.evaluate_player(
            session_id, player_id, data, coach_profile_id
        )
        return EvaluationResponse(
            attendance_id=attendance.id,
            player_id=attendance.player_id,
            convocation_id=attendance.convocation_id,
            technique_score=attendance.technique_score,
            physical_score=attendance.physical_score,
            attitude_score=attendance.attitude_score,
            feedback=attendance.feedback,
            feedback_generated_by_ai=attendance.feedback_generated_by_ai,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get(
    "/{session_id}/evaluations",
    response_model=list[EvaluationResponse],
)
async def get_session_evaluations(
    session_id: int,
    current_user: User = Depends(get_current_admin_or_coach),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene todas las evaluaciones de una sesión.
    Accesible por admin y coach.
    """
    try:
        service = EvaluationService(db)
        attendances = await service.get_session_evaluations(
            session_id, current_user.organization_id
        )
        return [
            EvaluationResponse(
                attendance_id=a.id,
                player_id=a.player_id,
                convocation_id=a.convocation_id,
                technique_score=a.technique_score,
                physical_score=a.physical_score,
                attitude_score=a.attitude_score,
                feedback=a.feedback,
                feedback_generated_by_ai=a.feedback_generated_by_ai,
            )
            for a in attendances
        ]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/{session_id}/players/{player_id}/evaluation",
    response_model=EvaluationResponse,
)
async def get_player_evaluation(
    session_id: int,
    player_id: int,
    current_user: User = Depends(get_current_admin_or_coach),
    db: AsyncSession = Depends(get_db),
):
    """Obtiene la evaluación de un jugador en una sesión."""
    try:
        service = EvaluationService(db)
        attendance = await service.get_player_evaluation(
            session_id, player_id, current_user.organization_id
        )
        return EvaluationResponse(
            attendance_id=attendance.id,
            player_id=attendance.player_id,
            convocation_id=attendance.convocation_id,
            technique_score=attendance.technique_score,
            physical_score=attendance.physical_score,
            attitude_score=attendance.attitude_score,
            feedback=attendance.feedback,
            feedback_generated_by_ai=attendance.feedback_generated_by_ai,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/{session_id}/players/{player_id}/generate-feedback",
    response_model=EvaluationResponse,
)
async def generate_feedback(
    session_id: int,
    player_id: int,
    current_user: User = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """
    Genera feedback personalizado para un jugador usando IA.
    Requiere que el jugador ya tenga evaluación registrada.
    El feedback se guarda en la asistencia y se marca como generado por IA.
    """
    try:
        from app.core.ai_feedback import generate_player_feedback
        from app.modules.players.models import Player
        from app.modules.training.models import Session

        # Verifica que el coach es el asignado
        session_service = SessionService(db)
        coach_profile_id = await session_service.get_coach_profile_id(
            current_user.id, current_user.organization_id
        )

        eval_service = EvaluationService(db)
        attendance = await eval_service.get_player_evaluation(
            session_id, player_id, current_user.organization_id
        )

        if attendance.technique_score is None:
            raise ValueError("Player has no evaluation yet — evaluate first")

        # Obtiene datos del jugador y sesión para el prompt
        player_result = await db.execute(select(Player).where(Player.id == player_id))
        player = player_result.scalar_one()

        session_result = await db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = session_result.scalar_one()

        if session.coach_id != coach_profile_id:
            raise ValueError("You are not assigned to this session")

        feedback = await generate_player_feedback(
            player_name=player.full_name,
            session_title=session.title,
            technique_score=attendance.technique_score,
            physical_score=attendance.physical_score,
            attitude_score=attendance.attitude_score,
            level=session.level.value,
            age_group=session.age_group,
        )

        attendance.feedback = feedback
        attendance.feedback_generated_by_ai = True
        await db.commit()
        await db.refresh(attendance)

        return EvaluationResponse(
            attendance_id=attendance.id,
            player_id=attendance.player_id,
            convocation_id=attendance.convocation_id,
            technique_score=attendance.technique_score,
            physical_score=attendance.physical_score,
            attitude_score=attendance.attitude_score,
            feedback=attendance.feedback,
            feedback_generated_by_ai=attendance.feedback_generated_by_ai,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
