import pytest


async def _create_admin_and_login(client) -> tuple[str, dict]:
    """Helper: registra admin y devuelve token y datos."""
    response = await client.post(
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
    return login.json()["access_token"], response.json()


@pytest.mark.asyncio
async def test_create_coach(client):
    """Admin puede crear un entrenador."""
    token, _ = await _create_admin_and_login(client)
    response = await client.post(
        "/api/v1/coaches",
        json={
            "email": "coach@test.com",
            "password": "password123",
            "full_name": "Test Coach",
            "phone": "600123456",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "coach@test.com"
    assert data["role"] == "coach"
    assert data["phone"] == "600123456"


@pytest.mark.asyncio
async def test_create_coach_unauthorized(client):
    """Sin token no se puede crear un entrenador."""
    response = await client.post(
        "/api/v1/coaches",
        json={
            "email": "coach@test.com",
            "password": "password123",
            "full_name": "Test Coach",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_coaches(client):
    """Admin puede listar entrenadores de su organización."""
    token, _ = await _create_admin_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/api/v1/coaches",
        json={
            "email": "coach1@test.com",
            "password": "password123",
            "full_name": "Coach One",
        },
        headers=headers,
    )

    await client.post(
        "/api/v1/coaches",
        json={
            "email": "coach2@test.com",
            "password": "password123",
            "full_name": "Coach Two",
        },
        headers=headers,
    )

    response = await client.get("/api/v1/coaches", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_coach_by_id(client):
    """Admin puede obtener un entrenador por ID."""
    token, _ = await _create_admin_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/coaches",
        json={
            "email": "coach@test.com",
            "password": "password123",
            "full_name": "Test Coach",
        },
        headers=headers,
    )
    coach_id = created.json()["id"]

    response = await client.get(f"/api/v1/coaches/{coach_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == coach_id


@pytest.mark.asyncio
async def test_update_coach(client):
    """Admin puede actualizar datos del entrenador."""
    token, _ = await _create_admin_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/coaches",
        json={
            "email": "coach@test.com",
            "password": "password123",
            "full_name": "Test Coach",
        },
        headers=headers,
    )
    coach_id = created.json()["id"]

    response = await client.patch(
        f"/api/v1/coaches/{coach_id}",
        json={"full_name": "Updated Coach", "bio": "Expert coach"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Coach"
    assert response.json()["bio"] == "Expert coach"


@pytest.mark.asyncio
async def test_deactivate_coach(client):
    """Admin puede desactivar un entrenador."""
    token, _ = await _create_admin_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/coaches",
        json={
            "email": "coach@test.com",
            "password": "password123",
            "full_name": "Test Coach",
        },
        headers=headers,
    )
    coach_id = created.json()["id"]

    response = await client.delete(f"/api/v1/coaches/{coach_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_get_coach_not_found(client):
    """Obtener un entrenador inexistente devuelve 404."""
    token, _ = await _create_admin_and_login(client)
    response = await client.get(
        "/api/v1/coaches/9999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
