import pytest

from app.modules.users.models import UserRole
from app.modules.users.schemas import (
    CoachCreateRequest,
    CoachUpdateRequest,
    LoginRequest,
    RegisterRequest,
)
from app.modules.users.service import AuthService, CoachService


@pytest.mark.asyncio
async def test_register_admin_creates_org(db_session):
    service = AuthService(db_session)
    user = await service.register(
        RegisterRequest(
            email="admin@test.com",
            password="password123",
            full_name="Test Admin",
            role=UserRole.ADMIN,
            organization_name="Test Org",
        )
    )
    assert user.role == UserRole.ADMIN
    assert user.organization_id is not None


@pytest.mark.asyncio
async def test_register_duplicate_email_raises(db_session):
    service = AuthService(db_session)
    data = RegisterRequest(
        email="admin@test.com",
        password="password123",
        full_name="Test Admin",
        role=UserRole.ADMIN,
        organization_name="Test Org",
    )
    await service.register(data)
    with pytest.raises(ValueError, match="Email already registered"):
        await service.register(data)


@pytest.mark.asyncio
async def test_login_success(db_session):
    service = AuthService(db_session)
    await service.register(
        RegisterRequest(
            email="admin@test.com",
            password="password123",
            full_name="Test Admin",
            role=UserRole.ADMIN,
            organization_name="Test Org",
        )
    )
    user, token = await service.login(
        LoginRequest(
            email="admin@test.com",
            password="password123",
        )
    )
    assert user.email == "admin@test.com"
    assert token is not None


@pytest.mark.asyncio
async def test_login_wrong_password_raises(db_session):
    service = AuthService(db_session)
    await service.register(
        RegisterRequest(
            email="admin@test.com",
            password="password123",
            full_name="Test Admin",
            role=UserRole.ADMIN,
            organization_name="Test Org",
        )
    )
    with pytest.raises(ValueError, match="Invalid credentials"):
        await service.login(
            LoginRequest(
                email="admin@test.com",
                password="wrongpassword",
            )
        )


@pytest.mark.asyncio
async def test_login_nonexistent_email_raises(db_session):
    service = AuthService(db_session)
    with pytest.raises(ValueError, match="Invalid credentials"):
        await service.login(
            LoginRequest(
                email="noexiste@test.com",
                password="password123",
            )
        )


@pytest.mark.asyncio
async def test_create_coach(db_session):
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
    user, profile = await coach_service.create_coach(
        CoachCreateRequest(
            email="coach@test.com",
            password="password123",
            full_name="Test Coach",
            phone="600000000",
        ),
        admin.organization_id,
    )
    assert user.role == UserRole.COACH
    assert profile.organization_id == admin.organization_id


@pytest.mark.asyncio
async def test_create_coach_duplicate_email_raises(db_session):
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
    data = CoachCreateRequest(
        email="coach@test.com",
        password="password123",
        full_name="Test Coach",
    )
    await coach_service.create_coach(data, admin.organization_id)
    with pytest.raises(ValueError, match="Email already registered"):
        await coach_service.create_coach(data, admin.organization_id)


@pytest.mark.asyncio
async def test_update_coach(db_session):
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
    _, profile = await coach_service.create_coach(
        CoachCreateRequest(
            email="coach@test.com",
            password="password123",
            full_name="Test Coach",
        ),
        admin.organization_id,
    )
    user, updated = await coach_service.update_coach(
        profile.id,
        admin.organization_id,
        CoachUpdateRequest(full_name="Updated Coach", bio="Expert"),
    )
    assert user.full_name == "Updated Coach"
    assert updated.bio == "Expert"


@pytest.mark.asyncio
async def test_deactivate_coach(db_session):
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
    _, profile = await coach_service.create_coach(
        CoachCreateRequest(
            email="coach@test.com",
            password="password123",
            full_name="Test Coach",
        ),
        admin.organization_id,
    )
    user, deactivated = await coach_service.deactivate_coach(
        profile.id, admin.organization_id
    )
    assert user.is_active is False
    assert deactivated.is_active is False


@pytest.mark.asyncio
async def test_get_coach_not_found(db_session):
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
    result = await coach_service.get_coach_by_id(9999, admin.organization_id)
    assert result is None


@pytest.mark.asyncio
async def test_list_coaches_pagination(db_session):
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
    for i in range(3):
        await coach_service.create_coach(
            CoachCreateRequest(
                email=f"coach{i}@test.com",
                password="password123",
                full_name=f"Coach {i}",
            ),
            admin.organization_id,
        )
    items, total = await coach_service.get_coaches(admin.organization_id)
    assert total == 3
    assert len(items) == 3


@pytest.mark.asyncio
async def test_update_coach_not_found_raises(db_session):
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
    with pytest.raises(ValueError, match="not found"):
        await coach_service.update_coach(
            9999, admin.organization_id, CoachUpdateRequest(full_name="XX")
        )


@pytest.mark.asyncio
async def test_deactivate_coach_not_found_raises(db_session):
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
    with pytest.raises(ValueError, match="not found"):
        await coach_service.deactivate_coach(9999, admin.organization_id)
