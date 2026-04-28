from datetime import date

from app.modules.organizations.models import Organization
from app.modules.players.models import GuardianPlayer, Player
from app.modules.users.models import (
    AdminProfile,
    CoachProfile,
    GuardianProfile,
    User,
    UserRole,
)


def test_organization_model():
    org = Organization(name="Academia FC", slug="academia-fc", is_active=True)
    assert org.name == "Academia FC"
    assert org.slug == "academia-fc"
    assert org.is_active is True
    assert repr(org) == "<Organization id=None slug=academia-fc>"


def test_user_model_admin():
    user = User(
        email="admin@academia.com",
        hashed_password="hashed",
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
    )
    assert user.role == UserRole.ADMIN
    assert user.is_active is True


def test_user_model_coach():
    user = User(
        email="coach@academia.com",
        hashed_password="hashed",
        full_name="Coach User",
        role=UserRole.COACH,
        is_active=True,
    )
    assert user.role == UserRole.COACH


def test_user_model_guardian():
    user = User(
        email="guardian@email.com",
        hashed_password="hashed",
        full_name="Guardian User",
        role=UserRole.GUARDIAN,
        is_active=True,
    )
    assert user.role == UserRole.GUARDIAN


def test_admin_profile_model():
    admin = AdminProfile(user_id=1, organization_id=1, is_active=True)
    assert admin.user_id == 1
    assert admin.is_active is True


def test_coach_profile_model():
    coach = CoachProfile(
        user_id=1, organization_id=1, phone="600123456", is_active=True
    )
    assert coach.phone == "600123456"
    assert coach.is_active is True


def test_guardian_profile_model():
    guardian = GuardianProfile(user_id=1, phone="600000001", is_active=True)
    assert guardian.user_id == 1
    assert guardian.is_active is True


def test_player_model():
    player = Player(
        full_name="Juan García",
        email="juan@email.com",
        organization_id=1,
        is_active=True,
        birth_date=date(2015, 6, 1),
    )
    assert player.is_minor is True
    assert player.phone is None


def test_guardian_player_relation():
    gp = GuardianPlayer(guardian_id=1, player_id=1)
    assert gp.guardian_id == 1
    assert gp.player_id == 1
