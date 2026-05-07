from datetime import UTC, date, datetime, timedelta

import pytest

from app.modules.attendance.models import AttendanceStatus, ConfirmedBy
from app.modules.attendance.service import AttendanceService
from app.modules.convocations.schemas import ConvocationCreateRequest
from app.modules.convocations.service import ConvocationService
from app.modules.players.schemas import PlayerCreateRequest
from app.modules.players.service import PlayerService
from app.modules.training.schemas import SessionCreateRequest
from app.modules.training.service import SessionService
from app.modules.users.models import UserRole
from app.modules.users.schemas import RegisterRequest
from app.modules.users.service import AuthService


async def _setup(db_session):
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

    return admin, player, session


@pytest.mark.asyncio
async def test_create_convocation(db_session):
    admin, player, session = await _setup(db_session)
    service = ConvocationService(db_session)
    deadline = datetime.now(UTC) + timedelta(days=2)
    convocation, attendances = await service.create_convocation(
        ConvocationCreateRequest(
            session_id=session.id,
            player_ids=[player.id],
            confirmation_deadline=deadline,
        ),
        admin.organization_id,
    )
    assert convocation.is_active is True
    assert len(attendances) == 1
    assert attendances[0].status == AttendanceStatus.PENDING


@pytest.mark.asyncio
async def test_create_convocation_past_deadline_raises(db_session):
    admin, player, session = await _setup(db_session)
    service = ConvocationService(db_session)
    deadline = datetime.now(UTC) - timedelta(hours=1)
    with pytest.raises(ValueError, match="future"):
        await service.create_convocation(
            ConvocationCreateRequest(
                session_id=session.id,
                player_ids=[player.id],
                confirmation_deadline=deadline,
            ),
            admin.organization_id,
        )


@pytest.mark.asyncio
async def test_duplicate_convocation_raises(db_session):
    admin, player, session = await _setup(db_session)
    service = ConvocationService(db_session)
    deadline = datetime.now(UTC) + timedelta(days=2)
    data = ConvocationCreateRequest(
        session_id=session.id,
        player_ids=[player.id],
        confirmation_deadline=deadline,
    )
    await service.create_convocation(data, admin.organization_id)
    with pytest.raises(ValueError, match="already exists"):
        await service.create_convocation(data, admin.organization_id)


@pytest.mark.asyncio
async def test_cancel_convocation(db_session):
    admin, player, session = await _setup(db_session)
    service = ConvocationService(db_session)
    deadline = datetime.now(UTC) + timedelta(days=2)
    convocation, _ = await service.create_convocation(
        ConvocationCreateRequest(
            session_id=session.id,
            player_ids=[player.id],
            confirmation_deadline=deadline,
        ),
        admin.organization_id,
    )
    cancelled = await service.cancel_convocation(convocation.id, admin.organization_id)
    assert cancelled.is_active is False


@pytest.mark.asyncio
async def test_get_confirmed_players(db_session):
    admin, player, session = await _setup(db_session)
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

    # Confirma via token
    att_service = AttendanceService(db_session)
    await att_service.confirm_via_token(
        attendances[0].confirmation_token, action="confirm"
    )

    confirmed = await conv_service.get_confirmed_players(
        convocation.id, admin.organization_id
    )
    assert len(confirmed) == 1
    assert confirmed[0].id == player.id


@pytest.mark.asyncio
async def test_confirm_via_token(db_session):
    admin, player, session = await _setup(db_session)
    conv_service = ConvocationService(db_session)
    deadline = datetime.now(UTC) + timedelta(days=2)
    _, attendances = await conv_service.create_convocation(
        ConvocationCreateRequest(
            session_id=session.id,
            player_ids=[player.id],
            confirmation_deadline=deadline,
        ),
        admin.organization_id,
    )

    att_service = AttendanceService(db_session)
    updated = await att_service.confirm_via_token(
        attendances[0].confirmation_token, action="confirm"
    )
    assert updated.status == AttendanceStatus.CONFIRMED
    assert updated.confirmed_by == ConfirmedBy.PLAYER


@pytest.mark.asyncio
async def test_reject_via_token(db_session):
    admin, player, session = await _setup(db_session)
    conv_service = ConvocationService(db_session)
    deadline = datetime.now(UTC) + timedelta(days=2)
    _, attendances = await conv_service.create_convocation(
        ConvocationCreateRequest(
            session_id=session.id,
            player_ids=[player.id],
            confirmation_deadline=deadline,
        ),
        admin.organization_id,
    )

    att_service = AttendanceService(db_session)
    updated = await att_service.confirm_via_token(
        attendances[0].confirmation_token, action="reject"
    )
    assert updated.status == AttendanceStatus.REJECTED


@pytest.mark.asyncio
async def test_invalid_token_raises(db_session):
    att_service = AttendanceService(db_session)
    with pytest.raises(ValueError, match="Invalid confirmation token"):
        await att_service.confirm_via_token("invalid_token", action="confirm")


@pytest.mark.asyncio
async def test_admin_confirm(db_session):
    admin, player, session = await _setup(db_session)
    conv_service = ConvocationService(db_session)
    deadline = datetime.now(UTC) + timedelta(days=2)
    convocation, _ = await conv_service.create_convocation(
        ConvocationCreateRequest(
            session_id=session.id,
            player_ids=[player.id],
            confirmation_deadline=deadline,
        ),
        admin.organization_id,
    )

    att_service = AttendanceService(db_session)
    updated = await att_service.admin_confirm(
        convocation.id, player.id, admin.organization_id
    )
    assert updated.status == AttendanceStatus.CONFIRMED
    assert updated.confirmed_by == ConfirmedBy.ADMIN


@pytest.mark.asyncio
async def test_expire_pending_attendances(db_session):
    admin, player, session = await _setup(db_session)
    # conv_service = ConvocationService(db_session)

    # Deadline en el pasado
    deadline = datetime.now(UTC) - timedelta(hours=1)

    # Saltamos la validación de fecha futura creando directamente
    from app.core.security import generate_confirmation_token
    from app.modules.attendance.models import Attendance
    from app.modules.convocations.models import Convocation

    convocation = Convocation(
        session_id=session.id,
        confirmation_deadline=deadline,
        is_active=True,
    )
    db_session.add(convocation)
    await db_session.flush()

    attendance = Attendance(
        convocation_id=convocation.id,
        player_id=player.id,
        confirmation_token=generate_confirmation_token(),
        status=AttendanceStatus.PENDING,
        feedback_generated_by_ai=False,
    )
    db_session.add(attendance)
    await db_session.commit()

    att_service = AttendanceService(db_session)
    expired_count = await att_service.expire_pending_attendances(convocation.id)
    assert expired_count == 1
