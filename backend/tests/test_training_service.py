from datetime import date

import pytest

from app.modules.training.models import SessionStatus
from app.modules.training.schemas import (
    SessionCreateRequest,
    SessionUpdateRequest,
)
from app.modules.training.service import SessionService
from app.modules.users.models import UserRole
from app.modules.users.schemas import CoachCreateRequest, RegisterRequest
from app.modules.users.service import AuthService, CoachService


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
    coach_service = CoachService(db_session)
    _, coach_profile = await coach_service.create_coach(
        CoachCreateRequest(
            email="coach@test.com",
            password="password123",
            full_name="Coach",
        ),
        admin.organization_id,
    )
    return admin, coach_profile


@pytest.mark.asyncio
async def test_create_session(db_session):
    admin, _ = await _setup(db_session)
    service = SessionService(db_session)
    session = await service.create_session(
        SessionCreateRequest(
            title="Test Session",
            session_date=date(2026, 12, 1),
            duration_minutes=90,
        ),
        admin.organization_id,
    )
    assert session.status == SessionStatus.DRAFT
    assert session.organization_id == admin.organization_id


@pytest.mark.asyncio
async def test_update_session_draft(db_session):
    admin, _ = await _setup(db_session)
    service = SessionService(db_session)
    session = await service.create_session(
        SessionCreateRequest(
            title="Test Session",
            session_date=date(2026, 12, 1),
            duration_minutes=90,
        ),
        admin.organization_id,
    )
    updated = await service.update_session(
        session.id,
        admin.organization_id,
        SessionUpdateRequest(title="Updated Session"),
    )
    assert updated.title == "Updated Session"


async def test_update_cancelled_session_raises(db_session):
    admin, _ = await _setup(db_session)
    service = SessionService(db_session)
    session = await service.create_session(
        SessionCreateRequest(
            title="Test Session",
            session_date=date(2026, 12, 1),
            duration_minutes=90,
        ),
        admin.organization_id,
    )
    await service.cancel_session(session.id, admin.organization_id)
    with pytest.raises(ValueError, match="Only DRAFT"):
        await service.update_session(
            session.id,
            admin.organization_id,
            SessionUpdateRequest(title="XX"),
        )


@pytest.mark.asyncio
async def test_cancel_session(db_session):
    admin, _ = await _setup(db_session)
    service = SessionService(db_session)
    session = await service.create_session(
        SessionCreateRequest(
            title="Test Session",
            session_date=date(2026, 12, 1),
            duration_minutes=90,
        ),
        admin.organization_id,
    )
    cancelled = await service.cancel_session(session.id, admin.organization_id)
    assert cancelled.status == SessionStatus.CANCELLED


@pytest.mark.asyncio
async def test_assign_coach(db_session):
    admin, coach_profile = await _setup(db_session)
    service = SessionService(db_session)
    session = await service.create_session(
        SessionCreateRequest(
            title="Test Session",
            session_date=date(2026, 12, 1),
            duration_minutes=90,
        ),
        admin.organization_id,
    )
    assigned = await service.assign_coach(
        session.id, admin.organization_id, coach_profile.id
    )
    assert assigned.status == SessionStatus.ASSIGNED
    assert assigned.coach_id == coach_profile.id


@pytest.mark.asyncio
async def test_full_lifecycle(db_session):
    admin, coach_profile = await _setup(db_session)
    service = SessionService(db_session)
    session = await service.create_session(
        SessionCreateRequest(
            title="Test Session",
            session_date=date(2026, 12, 1),
            duration_minutes=90,
        ),
        admin.organization_id,
    )
    await service.assign_coach(session.id, admin.organization_id, coach_profile.id)
    await service.accept_session(session.id, coach_profile.id)
    await service.start_session(session.id, coach_profile.id)
    completed = await service.complete_session(session.id, coach_profile.id)
    assert completed.status == SessionStatus.COMPLETED


@pytest.mark.asyncio
async def test_accept_wrong_coach_raises(db_session):
    admin, coach_profile = await _setup(db_session)
    service = SessionService(db_session)
    session = await service.create_session(
        SessionCreateRequest(
            title="Test Session",
            session_date=date(2026, 12, 1),
            duration_minutes=90,
        ),
        admin.organization_id,
    )
    await service.assign_coach(session.id, admin.organization_id, coach_profile.id)
    with pytest.raises(ValueError, match="not assigned"):
        await service.accept_session(session.id, 9999)


@pytest.mark.asyncio
async def test_add_content(db_session):
    admin, _ = await _setup(db_session)
    service = SessionService(db_session)
    session = await service.create_session(
        SessionCreateRequest(
            title="Test Session",
            session_date=date(2026, 12, 1),
            duration_minutes=90,
        ),
        admin.organization_id,
    )
    updated = await service.add_content(
        session.id, admin.organization_id, "Contenido de ejercicios"
    )
    assert updated.content == "Contenido de ejercicios"
    assert updated.content_generated_by_ai is False


@pytest.mark.asyncio
async def test_get_sessions_with_status_filter(db_session):
    admin, _ = await _setup(db_session)
    service = SessionService(db_session)

    await service.create_session(
        SessionCreateRequest(
            title="Session One",
            session_date=date(2026, 12, 1),
            duration_minutes=90,
        ),
        admin.organization_id,
    )
    s2 = await service.create_session(
        SessionCreateRequest(
            title="Session Two",
            session_date=date(2026, 12, 2),
            duration_minutes=60,
        ),
        admin.organization_id,
    )
    await service.cancel_session(s2.id, admin.organization_id)

    drafts, total = await service.get_sessions(
        admin.organization_id, status=SessionStatus.DRAFT
    )
    assert total == 1
    assert drafts[0].status == SessionStatus.DRAFT


@pytest.mark.asyncio
async def test_cancel_completed_session_raises(db_session):
    admin, coach_profile = await _setup(db_session)
    service = SessionService(db_session)
    session = await service.create_session(
        SessionCreateRequest(
            title="Test Session",
            session_date=date(2026, 12, 1),
            duration_minutes=90,
        ),
        admin.organization_id,
    )
    await service.assign_coach(session.id, admin.organization_id, coach_profile.id)
    await service.accept_session(session.id, coach_profile.id)
    await service.start_session(session.id, coach_profile.id)
    await service.complete_session(session.id, coach_profile.id)

    with pytest.raises(ValueError, match="Cannot cancel"):
        await service.cancel_session(session.id, admin.organization_id)


@pytest.mark.asyncio
async def test_session_not_found_returns_none(db_session):
    admin, _ = await _setup(db_session)
    service = SessionService(db_session)
    result = await service.get_session_by_id(9999, admin.organization_id)
    assert result is None
