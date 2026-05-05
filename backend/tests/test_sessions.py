import pytest


async def _setup(client) -> tuple[str, str, int, int]:
    """Helper: crea admin, coach, sesión. Devuelve admin_token, coach_token, coach_id, session_id."""
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

    return admin_token, coach_token, coach_id, session_id


@pytest.mark.asyncio
async def test_create_session(client):
    """Admin puede crear sesión en estado DRAFT."""
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

    response = await client.post(
        "/api/v1/sessions",
        json={
            "title": "Morning Training",
            "session_date": "2026-12-01",
            "duration_minutes": 60,
            "level": "beginner",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "draft"


@pytest.mark.asyncio
async def test_assign_coach(client):
    """Admin puede asignar entrenador — sesión pasa a ASSIGNED."""
    admin_token, _, coach_id, session_id = await _setup(client)

    response = await client.post(
        f"/api/v1/sessions/{session_id}/assign-coach",
        json={"coach_id": coach_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "assigned"
    assert response.json()["coach_id"] == coach_id


@pytest.mark.asyncio
async def test_coach_accepts_session(client):
    """Coach puede aceptar sesión asignada — pasa a ACCEPTED."""
    admin_token, coach_token, coach_id, session_id = await _setup(client)

    await client.post(
        f"/api/v1/sessions/{session_id}/assign-coach",
        json={"coach_id": coach_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = await client.post(
        f"/api/v1/sessions/{session_id}/accept",
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


@pytest.mark.asyncio
async def test_full_session_lifecycle(client):
    """Ciclo completo: DRAFT → ASSIGNED → ACCEPTED → IN_PROGRESS → COMPLETED."""
    admin_token, coach_token, coach_id, session_id = await _setup(client)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    coach_headers = {"Authorization": f"Bearer {coach_token}"}

    # Assign
    r = await client.post(
        f"/api/v1/sessions/{session_id}/assign-coach",
        json={"coach_id": coach_id},
        headers=admin_headers,
    )
    assert r.json()["status"] == "assigned"

    # Accept
    r = await client.post(
        f"/api/v1/sessions/{session_id}/accept",
        headers=coach_headers,
    )
    assert r.json()["status"] == "accepted"

    # Start
    r = await client.post(
        f"/api/v1/sessions/{session_id}/start",
        headers=coach_headers,
    )
    assert r.json()["status"] == "in_progress"

    # Complete
    r = await client.post(
        f"/api/v1/sessions/{session_id}/complete",
        headers=coach_headers,
    )
    assert r.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_add_content_to_session(client):
    """Admin puede añadir contenido a la sesión."""
    admin_token, _, _, session_id = await _setup(client)

    response = await client.patch(
        f"/api/v1/sessions/{session_id}/content",
        json={"content": "Warm up 10min, rondos 20min, partido 60min"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["content"] == "Warm up 10min, rondos 20min, partido 60min"


@pytest.mark.asyncio
async def test_assign_coach_wrong_status(client):
    """No se puede asignar coach a sesión que no está en DRAFT."""
    admin_token, _, coach_id, session_id = await _setup(client)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Cancela la sesión
    await client.delete(
        f"/api/v1/sessions/{session_id}",
        headers=admin_headers,
    )

    response = await client.post(
        f"/api/v1/sessions/{session_id}/assign-coach",
        json={"coach_id": coach_id},
        headers=admin_headers,
    )
    assert response.status_code == 400
