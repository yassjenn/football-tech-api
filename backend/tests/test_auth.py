import pytest

from app.core.security import create_access_token, hash_password, verify_password

# ── Tests de utilidades de seguridad ──────────────────────────


def test_hash_password():
    hashed = hash_password("mypassword123")
    assert hashed != "mypassword123"
    assert len(hashed) > 0


def test_verify_password_correct():
    hashed = hash_password("mypassword123")
    assert verify_password("mypassword123", hashed) is True


def test_verify_password_incorrect():
    hashed = hash_password("mypassword123")
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token():
    from app.core.security import decode_access_token

    token = create_access_token(subject="1", role="admin")
    payload = decode_access_token(token)
    assert payload["sub"] == "1"
    assert payload["role"] == "admin"


# ── Tests de endpoints ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_admin(client):
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
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "admin@test.com"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {
        "email": "duplicate@test.com",
        "password": "password123",
        "full_name": "Test User",
        "role": "admin",
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "logintest@test.com",
            "password": "password123",
            "full_name": "Login Test",
            "role": "admin",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "logintest@test.com",
            "password": "password123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpass@test.com",
            "password": "password123",
            "full_name": "Wrong Pass",
            "role": "admin",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrongpass@test.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
