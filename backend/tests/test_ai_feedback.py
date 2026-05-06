from datetime import UTC

import pytest

from app.core.config import settings


@pytest.mark.asyncio
async def test_generate_feedback_placeholder():
    """Cuando AI_ENABLED=False genera feedback de ejemplo sin llamar a OpenAI."""
    from unittest.mock import patch

    from app.core.ai_feedback import generate_player_feedback

    with patch.object(settings, "AI_ENABLED", False):
        feedback = await generate_player_feedback(
            player_name="Carlos García",
            session_title="Sesión técnica",
            technique_score=8,
            physical_score=6,
            attitude_score=9,
            level="intermediate",
            age_group="Sub-16",
        )
    assert feedback is not None
    assert "Carlos García" in feedback
    assert len(feedback) > 0


@pytest.mark.asyncio
async def test_generate_feedback_with_ai():
    """Genera feedback real con OpenAI si está disponible."""
    from app.core.ai_feedback import generate_player_feedback

    if not settings.AI_ENABLED or not settings.OPENAI_API_KEY:
        pytest.skip("AI disabled or no API key")

    feedback = await generate_player_feedback(
        player_name="Carlos García",
        session_title="Entrenamiento de pressing",
        technique_score=7,
        physical_score=8,
        attitude_score=9,
        level="intermediate",
        age_group="Sub-18",
    )
    assert feedback is not None
    assert len(feedback) > 50


@pytest.mark.asyncio
async def test_generate_feedback_endpoint(client):
    """Endpoint genera feedback y lo guarda en la evaluación."""
    from datetime import datetime, timedelta
    from unittest.mock import patch

    # Setup completo
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
    coach_headers = {"Authorization": f"Bearer {coach_token}"}

    player = await client.post(
        "/api/v1/players",
        json={
            "email": "player@test.com",
            "full_name": "Carlos García",
        },
        headers=admin_headers,
    )
    player_id = player.json()["id"]

    session = await client.post(
        "/api/v1/sessions",
        json={
            "title": "Sesión técnica",
            "session_date": "2026-12-01",
            "duration_minutes": 90,
            "level": "intermediate",
        },
        headers=admin_headers,
    )
    session_id = session.json()["id"]

    deadline = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    convocation = await client.post(
        "/api/v1/convocations",
        json={
            "session_id": session_id,
            "player_ids": [player_id],
            "confirmation_deadline": deadline,
        },
        headers=admin_headers,
    )
    convocation_id = convocation.json()["id"]

    await client.post(
        "/api/v1/attendance/admin-confirm",
        json={
            "player_id": player_id,
            "convocation_id": convocation_id,
        },
        headers=admin_headers,
    )

    await client.post(
        f"/api/v1/sessions/{session_id}/assign-coach",
        json={"coach_id": coach_id},
        headers=admin_headers,
    )
    await client.post(f"/api/v1/sessions/{session_id}/accept", headers=coach_headers)
    await client.post(f"/api/v1/sessions/{session_id}/start", headers=coach_headers)

    # Evalúa al jugador
    await client.post(
        f"/api/v1/sessions/{session_id}/players/{player_id}/evaluate",
        json={
            "technique_score": 8,
            "physical_score": 7,
            "attitude_score": 9,
        },
        headers=coach_headers,
    )

    # Genera feedback con AI desactivada
    with patch.object(settings, "AI_ENABLED", False):
        response = await client.post(
            f"/api/v1/sessions/{session_id}/players/{player_id}/generate-feedback",
            headers=coach_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["feedback"] is not None
    assert data["feedback_generated_by_ai"] is True
    assert "Carlos García" in data["feedback"]
