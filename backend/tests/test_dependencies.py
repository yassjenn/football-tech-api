import pytest


async def _register_and_login(
    client, email: str, role: str, password: str = "password123"
) -> str:
    """Helper: registra un usuario y devuelve su token."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test User",
            "role": role,
            "organization_name": "Test Org" if role == "admin" else None,
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_get_me_authenticated(client):
    """Usuario autenticado puede acceder a /me."""
    token = await _register_and_login(client, "admin@test.com", "admin")
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "admin@test.com"
    assert response.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client):
    """Sin token debe devolver 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(client):
    """Token inválido debe devolver 401."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer tokeninvalido"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_returns_correct_role(client):
    """El rol devuelto debe coincidir con el rol registrado."""
    token = await _register_and_login(client, "coach@test.com", "coach")
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "coach"
