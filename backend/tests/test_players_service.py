from datetime import date

import pytest

from app.modules.players.schemas import (
    GuardianCreateRequest,
    PlayerCreateRequest,
    PlayerUpdateRequest,
)
from app.modules.players.service import PlayerService
from app.modules.users.models import UserRole
from app.modules.users.schemas import RegisterRequest
from app.modules.users.service import AuthService


async def _create_admin(db_session):
    auth = AuthService(db_session)
    return await auth.register(
        RegisterRequest(
            email="admin@test.com",
            password="password123",
            full_name="Admin",
            role=UserRole.ADMIN,
            organization_name="Test Org",
        )
    )


@pytest.mark.asyncio
async def test_create_player(db_session):
    admin = await _create_admin(db_session)
    service = PlayerService(db_session)
    player = await service.create_player(
        PlayerCreateRequest(
            email="player@test.com",
            full_name="Test Player",
            birth_date=date(2010, 1, 1),
        ),
        admin.organization_id,
    )
    assert player.email == "player@test.com"
    assert player.is_minor is True


@pytest.mark.asyncio
async def test_create_player_duplicate_email_raises(db_session):
    admin = await _create_admin(db_session)
    service = PlayerService(db_session)
    data = PlayerCreateRequest(email="player@test.com", full_name="Player")
    await service.create_player(data, admin.organization_id)
    with pytest.raises(ValueError, match="already exists"):
        await service.create_player(data, admin.organization_id)


@pytest.mark.asyncio
async def test_update_player(db_session):
    admin = await _create_admin(db_session)
    service = PlayerService(db_session)
    player = await service.create_player(
        PlayerCreateRequest(email="player@test.com", full_name="Player"),
        admin.organization_id,
    )
    updated = await service.update_player(
        player.id,
        admin.organization_id,
        PlayerUpdateRequest(full_name="Updated", phone="600000000"),
    )
    assert updated.full_name == "Updated"
    assert updated.phone == "600000000"


@pytest.mark.asyncio
async def test_update_player_not_found_raises(db_session):
    admin = await _create_admin(db_session)
    service = PlayerService(db_session)
    with pytest.raises(ValueError, match="not found"):
        await service.update_player(
            9999, admin.organization_id, PlayerUpdateRequest(full_name="XX")
        )


@pytest.mark.asyncio
async def test_deactivate_player(db_session):
    admin = await _create_admin(db_session)
    service = PlayerService(db_session)
    player = await service.create_player(
        PlayerCreateRequest(email="player@test.com", full_name="Player"),
        admin.organization_id,
    )
    deactivated = await service.deactivate_player(player.id, admin.organization_id)
    assert deactivated.is_active is False


@pytest.mark.asyncio
async def test_assign_guardian_to_minor(db_session):
    admin = await _create_admin(db_session)
    service = PlayerService(db_session)
    player = await service.create_player(
        PlayerCreateRequest(
            email="minor@test.com",
            full_name="Minor",
            birth_date=date(2015, 1, 1),
        ),
        admin.organization_id,
    )
    user, profile = await service.create_and_assign_guardian(
        player.id,
        admin.organization_id,
        GuardianCreateRequest(
            email="guardian@test.com",
            full_name="Guardian",
            password="password123",
        ),
    )
    assert user.role == UserRole.GUARDIAN
    assert profile is not None


@pytest.mark.asyncio
async def test_assign_guardian_to_adult_raises(db_session):
    admin = await _create_admin(db_session)
    service = PlayerService(db_session)
    player = await service.create_player(
        PlayerCreateRequest(
            email="adult@test.com",
            full_name="Adult",
            birth_date=date(2000, 1, 1),
        ),
        admin.organization_id,
    )
    with pytest.raises(ValueError, match="not a minor"):
        await service.create_and_assign_guardian(
            player.id,
            admin.organization_id,
            GuardianCreateRequest(
                email="guardian@test.com",
                full_name="Guardian",
                password="password123",
            ),
        )


@pytest.mark.asyncio
async def test_get_player_guardians(db_session):
    admin = await _create_admin(db_session)
    service = PlayerService(db_session)
    player = await service.create_player(
        PlayerCreateRequest(
            email="minor@test.com",
            full_name="Minor",
            birth_date=date(2015, 1, 1),
        ),
        admin.organization_id,
    )
    await service.create_and_assign_guardian(
        player.id,
        admin.organization_id,
        GuardianCreateRequest(
            email="guardian@test.com",
            full_name="Guardian",
            password="password123",
        ),
    )
    guardians = await service.get_player_guardians(player.id, admin.organization_id)
    assert len(guardians) == 1
