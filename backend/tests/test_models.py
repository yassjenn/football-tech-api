from app.models.admin import Admin
from app.models.coach import Coach
from app.models.organization import Organization
from app.models.player import Player
from app.models.user import User, UserRole


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
        organization_id=1,
        is_active=True,
    )
    assert user.role == UserRole.ADMIN
    assert user.is_active is True
    assert "admin@academia.com" in repr(user)


def test_user_model_coach():
    user = User(
        email="coach@academia.com",
        hashed_password="hashed",
        full_name="Coach User",
        role=UserRole.COACH,
        organization_id=1,
        is_active=True,
    )
    assert user.role == UserRole.COACH


def test_coach_model():
    coach = Coach(user_id=1, organization_id=1, phone="600123456", is_active=True)
    assert coach.user_id == 1
    assert coach.is_active is True
    assert coach.phone == "600123456"


def test_player_model():
    player = Player(
        full_name="Juan García",
        email="juan@email.com",
        organization_id=1,
        is_active=True,
        is_verified=False,
    )
    assert player.full_name == "Juan García"
    assert player.is_active is True
    assert player.is_verified is False
    assert player.hashed_password is None
    assert player.phone is None
    assert "juan@email.com" in repr(player)


def test_admin_model():
    admin = Admin(user_id=1, organization_id=1, phone="600000001", is_active=True)
    assert admin.user_id == 1
    assert admin.is_active is True
    assert admin.phone == "600000001"
    assert repr(admin) == "<Admin id=None user_id=1>"
