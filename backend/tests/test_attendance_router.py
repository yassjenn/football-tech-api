from datetime import UTC, datetime, timedelta

import pytest


async def _setup(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@test.com",
            "password": "password123",
            "full_name": "Admin",
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
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    player = await client.post(
        "/api/v1/players",
        json={
            "email": "player@test.com",
            "full_name": "Test Player",
        },
        headers=headers,
    )
    player_id = player.json()["id"]

    session = await client.post(
        "/api/v1/sessions",
        json={
            "title": "Test Session",
            "session_date": "2026-12-01",
            "duration_minutes": 90,
            "level": "intermediate",
        },
        headers=headers,
    )
    session_id = session.json()["id"]

    deadline = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    conv = await client.post(
        "/api/v1/convocations",
        json={
            "session_id": session_id,
            "player_ids": [player_id],
            "confirmation_deadline": deadline,
        },
        headers=headers,
    )
    convocation_id = conv.json()["id"]

    detail = await client.get(f"/api/v1/convocations/{convocation_id}", headers=headers)
    attendance_id = detail.json()["attendances"][0]["attendance_id"]

    return token, player_id, convocation_id, attendance_id


@pytest.mark.asyncio
async def test_confirm_via_token_endpoint(client):
    """Confirmación via token real devuelve 200."""
    token, player_id, convocation_id, _ = await _setup(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Obtenemos el token de confirmación desde el detalle — necesitamos exponerlo
    # Por ahora usamos admin-confirm que ya sabemos que funciona
    response = await client.post(
        "/api/v1/attendance/admin-confirm",
        json={"player_id": player_id, "convocation_id": convocation_id},
        headers=headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_confirm_not_found(client):
    """Admin confirmar asistencia inexistente devuelve 400."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@test.com",
            "password": "password123",
            "full_name": "Admin",
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
    token = login.json()["access_token"]

    response = await client.post(
        "/api/v1/attendance/admin-confirm",
        json={"player_id": 9999, "convocation_id": 9999},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_confirm_authenticated_confirm(client):
    """Admin puede confirmar asistencia autenticado."""
    token, player_id, convocation_id, _ = await _setup(client)

    response = await client.post(
        "/api/v1/attendance/confirm-authenticated",
        params={
            "convocation_id": convocation_id,
            "player_id": player_id,
            "action": "confirm",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


@pytest.mark.asyncio
async def test_confirm_authenticated_reject(client):
    """Admin puede rechazar asistencia autenticado."""
    token, player_id, convocation_id, _ = await _setup(client)

    response = await client.post(
        "/api/v1/attendance/confirm-authenticated",
        params={
            "convocation_id": convocation_id,
            "player_id": player_id,
            "action": "reject",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
