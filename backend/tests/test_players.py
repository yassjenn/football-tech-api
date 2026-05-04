import pytest


async def _create_admin_and_login(client) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@test.com",
            "password": "password123",
            "full_name": "Test Admin",
            "role": "admin",
            "organization_name": "Test Academy",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@test.com",
            "password": "password123",
        },
    )
    return login.json()["access_token"]


@pytest.mark.asyncio
async def test_create_player(client):
    """Admin puede crear un jugador."""
    token = await _create_admin_and_login(client)
    response = await client.post(
        "/api/v1/players",
        json={
            "email": "player@test.com",
            "full_name": "Test Player",
            "birth_date": "2010-01-01",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "player@test.com"
    assert data["is_minor"] is True


@pytest.mark.asyncio
async def test_create_player_adult(client):
    """Jugador mayor de edad no es menor."""
    token = await _create_admin_and_login(client)
    response = await client.post(
        "/api/v1/players",
        json={
            "email": "adult@test.com",
            "full_name": "Adult Player",
            "birth_date": "2000-01-01",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["is_minor"] is False


@pytest.mark.asyncio
async def test_list_players(client):
    """Admin puede listar jugadores."""
    token = await _create_admin_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    for i in range(3):
        await client.post(
            "/api/v1/players",
            json={
                "email": f"player{i}@test.com",
                "full_name": f"Player {i}",
            },
            headers=headers,
        )

    response = await client.get("/api/v1/players", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 3


@pytest.mark.asyncio
async def test_update_player(client):
    """Admin puede actualizar datos del jugador."""
    token = await _create_admin_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/players",
        json={
            "email": "player@test.com",
            "full_name": "Test Player",
        },
        headers=headers,
    )
    player_id = created.json()["id"]

    response = await client.patch(
        f"/api/v1/players/{player_id}",
        json={"full_name": "Updated Player", "phone": "600000000"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Player"


@pytest.mark.asyncio
async def test_deactivate_player(client):
    """Admin puede desactivar un jugador."""
    token = await _create_admin_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/players",
        json={
            "email": "player@test.com",
            "full_name": "Test Player",
        },
        headers=headers,
    )
    player_id = created.json()["id"]

    response = await client.delete(f"/api/v1/players/{player_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_assign_guardian_to_minor(client):
    """Admin puede asignar guardian a jugador menor."""
    token = await _create_admin_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    player = await client.post(
        "/api/v1/players",
        json={
            "email": "minor@test.com",
            "full_name": "Minor Player",
            "birth_date": "2015-01-01",
        },
        headers=headers,
    )
    player_id = player.json()["id"]

    response = await client.post(
        f"/api/v1/players/{player_id}/guardians",
        json={
            "email": "guardian@test.com",
            "full_name": "Test Guardian",
            "phone": "600000001",
            "password": "password123",
        },
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["email"] == "guardian@test.com"


@pytest.mark.asyncio
async def test_assign_guardian_to_adult_fails(client):
    """No se puede asignar guardian a jugador mayor de edad."""
    token = await _create_admin_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    player = await client.post(
        "/api/v1/players",
        json={
            "email": "adult@test.com",
            "full_name": "Adult Player",
            "birth_date": "2000-01-01",
        },
        headers=headers,
    )
    player_id = player.json()["id"]

    response = await client.post(
        f"/api/v1/players/{player_id}/guardians",
        json={
            "email": "guardian@test.com",
            "full_name": "Test Guardian",
            "password": "password123",
        },
        headers=headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_player_guardians(client):
    """Admin puede ver los guardians de un jugador."""
    token = await _create_admin_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    player = await client.post(
        "/api/v1/players",
        json={
            "email": "minor@test.com",
            "full_name": "Minor Player",
            "birth_date": "2015-01-01",
        },
        headers=headers,
    )
    player_id = player.json()["id"]

    await client.post(
        f"/api/v1/players/{player_id}/guardians",
        json={
            "email": "guardian@test.com",
            "full_name": "Test Guardian",
            "password": "password123",
        },
        headers=headers,
    )

    response = await client.get(
        f"/api/v1/players/{player_id}/guardians", headers=headers
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
