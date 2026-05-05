from datetime import UTC, datetime, timedelta

import pytest


async def _setup(client) -> tuple[str, str, int, int, int]:
    """
    Helper completo: admin, coach, jugador, sesión en IN_PROGRESS con asistencia CONFIRMED.
    Devuelve admin_token, coach_token, coach_id, session_id, player_id.
    """
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
    admin_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@test.com",
            "password": "password123",
        },
    )
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Coach
    coach = await client.post(
        "/api/v1/coaches",
        json={
            "email": "coach@test.com",
            "password": "password123",
            "full_name": "Test Coach",
        },
        headers=admin_headers,
    )
    coach_id = coach.json()["id"]

    coach_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "coach@test.com",
            "password": "password123",
        },
    )
    coach_token = coach_login.json()["access_token"]
    coach_headers = {"Authorization": f"Bearer {coach_token}"}

    # Jugador
    player = await client.post(
        "/api/v1/players",
        json={
            "email": "player@test.com",
            "full_name": "Test Player",
        },
        headers=admin_headers,
    )
    player_id = player.json()["id"]

    # Sesión
    session = await client.post(
        "/api/v1/sessions",
        json={
            "title": "Test Session",
            "session_date": "2026-12-01",
            "duration_minutes": 90,
            "level": "intermediate",
        },
        headers=admin_headers,
    )
    session_id = session.json()["id"]

    # Convocatoria con confirmación
    deadline = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    await client.post(
        "/api/v1/convocations",
        json={
            "session_id": session_id,
            "player_ids": [player_id],
            "confirmation_deadline": deadline,
        },
        headers=admin_headers,
    )

    # Admin confirma asistencia manualmente
    await client.post(
        "/api/v1/attendance/admin-confirm",
        json={
            "player_id": player_id,
            "convocation_id": 1,
        },
        headers=admin_headers,
    )

    # Ciclo de sesión hasta IN_PROGRESS
    await client.post(
        f"/api/v1/sessions/{session_id}/assign-coach",
        json={"coach_id": coach_id},
        headers=admin_headers,
    )
    await client.post(
        f"/api/v1/sessions/{session_id}/accept",
        headers=coach_headers,
    )
    await client.post(
        f"/api/v1/sessions/{session_id}/start",
        headers=coach_headers,
    )

    return admin_token, coach_token, coach_id, session_id, player_id


@pytest.mark.asyncio
async def test_evaluate_player(client):
    """Coach puede evaluar a un jugador confirmado."""
    _, coach_token, _, session_id, player_id = await _setup(client)

    response = await client.post(
        f"/api/v1/sessions/{session_id}/players/{player_id}/evaluate",
        json={
            "technique_score": 8,
            "physical_score": 7,
            "attitude_score": 9,
            "feedback": "Buen trabajo, mejorar el primer toque.",
        },
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["technique_score"] == 8
    assert data["physical_score"] == 7
    assert data["attitude_score"] == 9
    assert data["feedback_generated_by_ai"] is False


@pytest.mark.asyncio
async def test_evaluate_invalid_score(client):
    """Puntuación fuera de rango devuelve 422."""
    _, coach_token, _, session_id, player_id = await _setup(client)

    response = await client.post(
        f"/api/v1/sessions/{session_id}/players/{player_id}/evaluate",
        json={
            "technique_score": 15,
            "physical_score": 7,
            "attitude_score": 9,
        },
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_session_evaluations(client):
    """Admin puede ver todas las evaluaciones de una sesión."""
    admin_token, coach_token, _, session_id, player_id = await _setup(client)

    await client.post(
        f"/api/v1/sessions/{session_id}/players/{player_id}/evaluate",
        json={
            "technique_score": 8,
            "physical_score": 7,
            "attitude_score": 9,
        },
        headers={"Authorization": f"Bearer {coach_token}"},
    )

    response = await client.get(
        f"/api/v1/sessions/{session_id}/evaluations",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_player_evaluation(client):
    """Admin puede ver la evaluación de un jugador específico."""
    admin_token, coach_token, _, session_id, player_id = await _setup(client)

    await client.post(
        f"/api/v1/sessions/{session_id}/players/{player_id}/evaluate",
        json={
            "technique_score": 8,
            "physical_score": 7,
            "attitude_score": 9,
            "feedback": "Muy bien.",
        },
        headers={"Authorization": f"Bearer {coach_token}"},
    )

    response = await client.get(
        f"/api/v1/sessions/{session_id}/players/{player_id}/evaluation",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["feedback"] == "Muy bien."


@pytest.mark.asyncio
async def test_evaluate_unconfirmed_player(client):
    """No se puede evaluar a un jugador sin asistencia confirmada."""
    admin_token, coach_token, coach_id, _, _ = await _setup(client)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    coach_headers = {"Authorization": f"Bearer {coach_token}"}

    # Crea un jugador nuevo sin confirmar
    player2 = await client.post(
        "/api/v1/players",
        json={
            "email": "player2@test.com",
            "full_name": "Player Two",
        },
        headers=admin_headers,
    )
    player2_id = player2.json()["id"]

    # Nueva sesión completa
    session2 = await client.post(
        "/api/v1/sessions",
        json={
            "title": "Session 2",
            "session_date": "2026-12-02",
            "duration_minutes": 60,
            "level": "intermediate",
        },
        headers=admin_headers,
    )
    session2_id = session2.json()["id"]

    from datetime import datetime, timedelta

    deadline = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    await client.post(
        "/api/v1/convocations",
        json={
            "session_id": session2_id,
            "player_ids": [player2_id],
            "confirmation_deadline": deadline,
        },
        headers=admin_headers,
    )

    await client.post(
        f"/api/v1/sessions/{session2_id}/assign-coach",
        json={"coach_id": coach_id},
        headers=admin_headers,
    )
    await client.post(
        f"/api/v1/sessions/{session2_id}/accept",
        headers=coach_headers,
    )
    await client.post(
        f"/api/v1/sessions/{session2_id}/start",
        headers=coach_headers,
    )

    response = await client.post(
        f"/api/v1/sessions/{session2_id}/players/{player2_id}/evaluate",
        json={"technique_score": 8, "physical_score": 7, "attitude_score": 9},
        headers=coach_headers,
    )
    assert response.status_code == 400
