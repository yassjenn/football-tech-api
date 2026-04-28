from datetime import date

from app.modules.organizations.models import Organization
from app.modules.players.models import GuardianPlayer, Player
from app.modules.users.models import (
    AdminProfile,
    CoachProfile,
    GuardianProfile,
    PlayerProfile,
    User,
    UserRole,
)


def test_organization_model():
    org = Organization(name="Academia FC", slug="academia-fc", is_active=True)
    assert org.name == "Academia FC"
    assert org.slug == "academia-fc"
    assert org.is_active is True
    assert repr(org) == "<Organization id=None slug=academia-fc>"


def test_user_role_values():
    """Verifica que todos los roles del sistema están definidos."""
    assert UserRole.ADMIN == "admin"
    assert UserRole.COACH == "coach"
    assert UserRole.GUARDIAN == "guardian"
    assert UserRole.PLAYER == "player"


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


def test_user_model_player():
    user = User(
        email="player@academia.com",
        hashed_password="hashed",
        full_name="Player User",
        role=UserRole.PLAYER,
        is_active=True,
    )
    assert user.role == UserRole.PLAYER


def test_admin_profile_model():
    admin = AdminProfile(user_id=1, organization_id=1, is_active=True)
    assert admin.user_id == 1
    assert admin.is_active is True


def test_coach_profile_model():
    coach = CoachProfile(
        user_id=1, organization_id=1, phone="600123456", is_active=True
    )
    assert coach.phone == "600123456"


def test_guardian_profile_model():
    guardian = GuardianProfile(user_id=1, phone="600000001", is_active=True)
    assert guardian.user_id == 1


def test_player_profile_is_minor_true():
    """Jugador menor de 18 años."""
    profile = PlayerProfile(
        user_id=1,
        organization_id=1,
        birth_date=date(2015, 6, 1),
        is_active=True,
    )
    assert profile.is_minor is True


def test_player_profile_is_minor_false():
    """Jugador mayor de 18 años."""
    profile = PlayerProfile(
        user_id=1,
        organization_id=1,
        birth_date=date(2000, 1, 1),
        is_active=True,
    )
    assert profile.is_minor is False


def test_player_profile_no_birthdate():
    """Sin fecha de nacimiento se asume mayor de edad."""
    profile = PlayerProfile(user_id=1, organization_id=1, is_active=True)
    assert profile.is_minor is False


def test_player_domain_model():
    """Player de dominio sin cuenta (menor de edad)."""
    player = Player(
        full_name="Niño García",
        email="nino@academia.com",
        organization_id=1,
        is_active=True,
    )
    assert player.user_id is None  # sin cuenta, es menor
    assert player.is_active is True


def test_player_domain_model_with_user():
    """Player de dominio con cuenta (mayor de edad)."""
    player = Player(
        full_name="Mayor García",
        email="mayor@academia.com",
        organization_id=1,
        is_active=True,
        user_id=5,
    )
    assert player.user_id == 5


def test_guardian_player_relation():
    gp = GuardianPlayer(guardian_id=1, player_id=1)
    assert gp.guardian_id == 1
    assert gp.player_id == 1
