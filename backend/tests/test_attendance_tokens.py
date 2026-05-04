from datetime import UTC, datetime, timedelta

import pytest

from app.core.security import (
    create_confirmation_jwt,
    decode_confirmation_jwt,
    generate_confirmation_token,
)
from app.modules.attendance.models import AttendanceStatus, ConfirmedBy
from app.modules.attendance.service import AttendanceService
from app.modules.convocations.models import Convocation
from app.modules.organizations.models import Organization
from app.modules.players.models import Player
from app.modules.training.models import Session, SessionLevel, SessionStatus

# ── Tests de utilidades de token ──────────────────────────────


def test_generate_confirmation_token():
    """El token debe ser único y suficientemente largo."""
    token1 = generate_confirmation_token()
    token2 = generate_confirmation_token()
    assert token1 != token2
    assert len(token1) > 20


def test_create_and_decode_confirmation_jwt():
    """El JWT de confirmación debe codificar y decodificar correctamente."""
    jwt_token = create_confirmation_jwt(attendance_id=42, expires_hours=48)
    payload = decode_confirmation_jwt(jwt_token)
    assert payload["sub"] == "42"
    assert payload["type"] == "attendance_confirmation"


def test_decode_invalid_confirmation_jwt():
    """Un JWT de auth no debe ser válido como token de confirmación."""
    from jose import JWTError

    from app.core.security import create_access_token

    auth_token = create_access_token(subject="1", role="admin")
    with pytest.raises(JWTError):
        decode_confirmation_jwt(auth_token)


# ── Tests de servicio de confirmación ─────────────────────────


@pytest.mark.asyncio
async def test_confirm_via_token(client, db_session):
    """Confirmar asistencia via token debe actualizar el estado."""
    # Setup: organización, sesión, convocatoria, jugador, asistencia
    org = Organization(name="Test Org", slug="test-org", is_active=True)
    db_session.add(org)
    await db_session.flush()

    player = Player(
        full_name="Test Player",
        email="player@test.com",
        organization_id=org.id,
        is_active=True,
    )
    db_session.add(player)
    await db_session.flush()

    session = Session(
        title="Test Session",
        session_date=datetime.now(UTC).date(),
        organization_id=org.id,
        status=SessionStatus.DRAFT,
        level=SessionLevel.INTERMEDIATE,
        content_generated_by_ai=False,
    )
    db_session.add(session)
    await db_session.flush()

    convocation = Convocation(
        session_id=session.id,
        confirmation_deadline=datetime.now(UTC) + timedelta(hours=24),
        is_active=True,
    )
    db_session.add(convocation)
    await db_session.flush()

    service = AttendanceService(db_session)
    attendance = await service.create_attendance(
        convocation_id=convocation.id,
        player_id=player.id,
    )

    # Confirma via token
    updated = await service.confirm_via_token(
        attendance.confirmation_token, confirm=True
    )
    assert updated.status == AttendanceStatus.CONFIRMED
    assert updated.confirmed_by == ConfirmedBy.PLAYER
    assert updated.confirmed_at is not None


@pytest.mark.asyncio
async def test_confirm_expired_convocation(client, db_session):
    """Confirmar después del plazo debe lanzar error y marcar como EXPIRED."""
    org = Organization(name="Test Org 2", slug="test-org-2", is_active=True)
    db_session.add(org)
    await db_session.flush()

    player = Player(
        full_name="Test Player 2",
        email="player2@test.com",
        organization_id=org.id,
        is_active=True,
    )
    db_session.add(player)
    await db_session.flush()

    session = Session(
        title="Expired Session",
        session_date=datetime.now(UTC).date(),
        organization_id=org.id,
        status=SessionStatus.DRAFT,
        level=SessionLevel.INTERMEDIATE,
        content_generated_by_ai=False,
    )
    db_session.add(session)
    await db_session.flush()

    # Convocatoria ya expirada
    convocation = Convocation(
        session_id=session.id,
        confirmation_deadline=datetime.now(UTC) - timedelta(hours=1),
        is_active=True,
    )
    db_session.add(convocation)
    await db_session.flush()

    service = AttendanceService(db_session)
    attendance = await service.create_attendance(
        convocation_id=convocation.id,
        player_id=player.id,
    )

    with pytest.raises(ValueError, match="deadline"):
        await service.confirm_via_token(attendance.confirmation_token, confirm=True)
