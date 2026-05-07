from datetime import UTC, date, datetime, timedelta

import pytest

from app.modules.attendance.service import AttendanceService
from app.modules.convocations.schemas import ConvocationCreateRequest
from app.modules.convocations.service import ConvocationService
from app.modules.evaluations.schemas import EvaluationCreateRequest
from app.modules.evaluations.service import EvaluationService
from app.modules.players.schemas import PlayerCreateRequest
from app.modules.players.service import PlayerService
from app.modules.training.schemas import SessionCreateRequest
from app.modules.training.service import SessionService
from app.modules.users.models import UserRole
from app.modules.users.schemas import CoachCreateRequest, RegisterRequest
from app.modules.users.service import AuthService, CoachService


async def _setup(db_session):
    """Setup completo con sesión en IN_PROGRESS y asistencia CONFIRMED."""
    auth = AuthService(db_session)
    admin = await auth.register(
        RegisterRequest(
            email="admin@test.com",
            password="password123",
            full_name="Admin",
            role=UserRole.ADMIN,
            organization_name="Test Org",
        )
    )

    coach_service = CoachService(db_session)
    _, coach_profile = await coach_service.create_coach(
        CoachCreateRequest(
            email="coach@test.com",
            password="password123",
            full_name="Coach",
        ),
        admin.organization_id,
    )

    player_service = PlayerService(db_session)
    player = await player_service.create_player(
        PlayerCreateRequest(email="player@test.com", full_name="Player"),
        admin.organization_id,
    )

    session_service = SessionService(db_session)
    session = await session_service.create_session(
        SessionCreateRequest(
            title="Test Session",
            session_date=date(2026, 12, 1),
            duration_minutes=90,
        ),
        admin.organization_id,
    )

    conv_service = ConvocationService(db_session)
    deadline = datetime.now(UTC) + timedelta(days=2)
    convocation, attendances = await conv_service.create_convocation(
        ConvocationCreateRequest(
            session_id=session.id,
            player_ids=[player.id],
            confirmation_deadline=deadline,
        ),
        admin.organization_id,
    )

    att_service = AttendanceService(db_session)
    await att_service.confirm_via_token(
        attendances[0].confirmation_token, action="confirm"
    )

    await session_service.assign_coach(
        session.id, admin.organization_id, coach_profile.id
    )
    await session_service.accept_session(session.id, coach_profile.id)
    await session_service.start_session(session.id, coach_profile.id)

    return admin, coach_profile, player, session


@pytest.mark.asyncio
async def test_evaluate_player(db_session):
    _, coach_profile, player, session = await _setup(db_session)
    service = EvaluationService(db_session)
    attendance = await service.evaluate_player(
        session.id,
        player.id,
        EvaluationCreateRequest(
            technique_score=8,
            physical_score=7,
            attitude_score=9,
        ),
        coach_profile.id,
    )
    assert attendance.technique_score == 8
    assert attendance.physical_score == 7
    assert attendance.attitude_score == 9
    assert attendance.feedback_generated_by_ai is False


@pytest.mark.asyncio
async def test_evaluate_wrong_coach_raises(db_session):
    _, _, player, session = await _setup(db_session)
    service = EvaluationService(db_session)
    with pytest.raises(ValueError, match="not assigned"):
        await service.evaluate_player(
            session.id,
            player.id,
            EvaluationCreateRequest(
                technique_score=8,
                physical_score=7,
                attitude_score=9,
            ),
            coach_profile_id=9999,
        )


@pytest.mark.asyncio
async def test_evaluate_session_wrong_status_raises(db_session):
    admin, coach_profile, player, session = await _setup(db_session)
    session_service = SessionService(db_session)
    await session_service.complete_session(session.id, coach_profile.id)

    # Intenta evaluar desde COMPLETED — sí está permitido
    service = EvaluationService(db_session)
    attendance = await service.evaluate_player(
        session.id,
        player.id,
        EvaluationCreateRequest(
            technique_score=8,
            physical_score=7,
            attitude_score=9,
        ),
        coach_profile.id,
    )
    assert attendance.technique_score == 8


@pytest.mark.asyncio
async def test_get_session_evaluations(db_session):
    _, coach_profile, player, session = await _setup(db_session)
    eval_service = EvaluationService(db_session)
    # admin_obj, _, _, _ = (None, None, None, None)

    # Evalúa al jugador
    service = EvaluationService(db_session)
    await service.evaluate_player(
        session.id,
        player.id,
        EvaluationCreateRequest(
            technique_score=8,
            physical_score=7,
            attitude_score=9,
        ),
        coach_profile.id,
    )

    # auth = AuthService(db_session)
    from sqlalchemy import select

    from app.modules.users.models import User

    result = await db_session.execute(
        select(User).where(User.email == "admin@test.com")
    )
    admin_user = result.scalar_one()

    evaluations = await eval_service.get_session_evaluations(
        session.id, admin_user.organization_id
    )
    assert len(evaluations) == 1


@pytest.mark.asyncio
async def test_get_player_evaluation(db_session):
    admin, coach_profile, player, session = await _setup(db_session)
    service = EvaluationService(db_session)

    await service.evaluate_player(
        session.id,
        player.id,
        EvaluationCreateRequest(
            technique_score=8,
            physical_score=7,
            attitude_score=9,
            feedback="Muy bien.",
        ),
        coach_profile.id,
    )

    attendance = await service.get_player_evaluation(
        session.id, player.id, admin.organization_id
    )
    assert attendance.feedback == "Muy bien."
