import pytest

from app.core.config import settings
from app.modules.training.models import SessionLevel


@pytest.mark.asyncio
async def test_generate_content_placeholder():
    """Cuando AI_ENABLED=False genera contenido de ejemplo sin llamar a OpenAI."""
    from unittest.mock import patch

    from app.core.ai_content import generate_session_content

    with patch.object(settings, "AI_ENABLED", False):
        content = await generate_session_content(
            title="Sesión de prueba",
            duration_minutes=90,
            level=SessionLevel.INTERMEDIATE,
            age_group="Sub-16",
        )
    assert content is not None
    assert len(content) > 0
    assert "Sesión de prueba" in content


@pytest.mark.asyncio
async def test_generate_content_with_ai():
    """Genera contenido real con OpenAI si está disponible."""
    from app.core.ai_content import generate_session_content

    if not settings.AI_ENABLED or not settings.OPENAI_API_KEY:
        pytest.skip("AI disabled or no API key")

    content = await generate_session_content(
        title="Entrenamiento de pressing",
        duration_minutes=90,
        level=SessionLevel.INTERMEDIATE,
        age_group="Sub-18",
        description="Foco en presión alta tras pérdida de balón",
    )
    assert content is not None
    assert len(content) > 100  # Respuesta sustancial


@pytest.mark.asyncio
async def test_generate_content_endpoint(client):
    """Endpoint genera contenido y lo guarda en la sesión."""
    # Setup admin y sesión
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

    session = await client.post(
        "/api/v1/sessions",
        json={
            "title": "Sesión técnica",
            "session_date": "2026-12-01",
            "duration_minutes": 90,
            "level": "intermediate",
            "age_group": "Sub-16",
        },
        headers=headers,
    )
    session_id = session.json()["id"]

    # Desactiva AI para el test de endpoint — no queremos llamadas reales en CI
    from unittest.mock import patch

    with patch.object(settings, "AI_ENABLED", False):
        response = await client.post(
            f"/api/v1/sessions/{session_id}/generate-content",
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["content"] is not None
    assert data["content_generated_by_ai"] is True
