from fastapi import APIRouter, Depends, HTTPException, status
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
