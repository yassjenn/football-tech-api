from datetime import date

from app.models.attendance import ConfirmedBy
from app.models.guardian import Guardian
from app.models.guardian_player import GuardianPlayer
from app.models.player import Player


def test_guardian_model():
    """Verifica que Guardian se instancia correctamente."""
    guardian = Guardian(
        full_name="Carlos García",
        email="carlos@email.com",
        is_active=True,
        is_verified=False,
    )
    assert guardian.full_name == "Carlos García"
    assert guardian.is_active is True
    assert guardian.is_verified is False
    assert guardian.hashed_password is None
    assert repr(guardian) == "<Guardian id=None email=carlos@email.com>"


def test_guardian_player_relation():
    """Verifica que la tabla intermedia se instancia correctamente."""
    gp = GuardianPlayer(guardian_id=1, player_id=1)
    assert gp.guardian_id == 1
    assert gp.player_id == 1


def test_player_is_minor_true():
    """Verifica que un jugador menor de 18 años se detecta correctamente."""
    player = Player(
        full_name="Niño García",
        email="nino@email.com",
        organization_id=1,
        is_active=True,
        is_verified=False,
        birth_date=date(2015, 6, 1),  # 10 años
    )
    assert player.is_minor is True


def test_player_is_minor_false():
    """Verifica que un jugador mayor de 18 años no es menor."""
    player = Player(
        full_name="Mayor García",
        email="mayor@email.com",
        organization_id=1,
        is_active=True,
        is_verified=False,
        birth_date=date(2000, 1, 1),  # > 18 años
    )
    assert player.is_minor is False


def test_player_is_minor_no_birthdate():
    """Sin fecha de nacimiento se asume mayor de edad."""
    player = Player(
        full_name="Sin Fecha",
        email="sinfecha@email.com",
        organization_id=1,
        is_active=True,
        is_verified=False,
    )
    assert player.is_minor is False


def test_confirmed_by_guardian():
    """Verifica que el enum ConfirmedBy incluye GUARDIAN."""
    assert ConfirmedBy.GUARDIAN == "guardian"
    assert ConfirmedBy.PLAYER == "player"
    assert ConfirmedBy.ADMIN == "admin"
