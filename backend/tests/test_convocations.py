from datetime import UTC, datetime, timedelta

import pytest


async def _setup(client) -> tuple[str, int, int]:
    """Helper: crea admin, jugador y sesión. Devuelve token, player_id, session_id."""
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

    return token, player_id, session_id


@pytest.mark.asyncio
async def test_create_convocation(client):
    """Admin puede crear una convocatoria."""
    token, player_id, session_id = await _setup(client)
    deadline = (datetime.now(UTC) + timedelta(days=2)).isoformat()

    response = await client.post(
        "/api/v1/convocations",
        json={
            "session_id": session_id,
            "player_ids": [player_id],
            "confirmation_deadline": deadline,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["session_id"] == session_id
    assert data["total_players"] == 1
    assert data["pending"] == 1


@pytest.mark.asyncio
async def test_create_convocation_past_deadline(client):
    """No se puede crear convocatoria con fecha límite pasada."""
    token, player_id, session_id = await _setup(client)
    deadline = (datetime.now(UTC) - timedelta(hours=1)).isoformat()

    response = await client.post(
        "/api/v1/convocations",
        json={
            "session_id": session_id,
            "player_ids": [player_id],
            "confirmation_deadline": deadline,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_duplicate_convocation(client):
    """No se puede crear dos convocatorias para la misma sesión."""
    token, player_id, session_id = await _setup(client)
    headers = {"Authorization": f"Bearer {token}"}
    deadline = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    payload = {
        "session_id": session_id,
        "player_ids": [player_id],
        "confirmation_deadline": deadline,
    }

    await client.post("/api/v1/convocations", json=payload, headers=headers)
    response = await client.post("/api/v1/convocations", json=payload, headers=headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_convocations(client):
    """Admin puede listar convocatorias."""
    token, player_id, session_id = await _setup(client)
    headers = {"Authorization": f"Bearer {token}"}
    deadline = (datetime.now(UTC) + timedelta(days=2)).isoformat()

    await client.post(
        "/api/v1/convocations",
        json={
            "session_id": session_id,
            "player_ids": [player_id],
            "confirmation_deadline": deadline,
        },
        headers=headers,
    )

    response = await client.get("/api/v1/convocations", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_convocation_detail(client):
    """Admin puede ver el detalle de una convocatoria con asistencias."""
    token, player_id, session_id = await _setup(client)
    headers = {"Authorization": f"Bearer {token}"}
    deadline = (datetime.now(UTC) + timedelta(days=2)).isoformat()

    created = await client.post(
        "/api/v1/convocations",
        json={
            "session_id": session_id,
            "player_ids": [player_id],
            "confirmation_deadline": deadline,
        },
        headers=headers,
    )
    conv_id = created.json()["id"]

    response = await client.get(f"/api/v1/convocations/{conv_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["attendances"]) == 1
    assert data["attendances"][0]["status"] == "pending"


@pytest.mark.asyncio
async def test_cancel_convocation(client):
    """Admin puede cancelar una convocatoria."""
    token, player_id, session_id = await _setup(client)
    headers = {"Authorization": f"Bearer {token}"}
    deadline = (datetime.now(UTC) + timedelta(days=2)).isoformat()

    created = await client.post(
        "/api/v1/convocations",
        json={
            "session_id": session_id,
            "player_ids": [player_id],
            "confirmation_deadline": deadline,
        },
        headers=headers,
    )
    conv_id = created.json()["id"]

    response = await client.delete(f"/api/v1/convocations/{conv_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False
