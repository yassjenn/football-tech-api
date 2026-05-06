import pytest


@pytest.mark.asyncio
async def test_openai_connection():
    """Verifica que OpenAI está disponible con la API key configurada."""
    from app.core.ai import check_openai_connection
    from app.core.config import settings

    if not settings.AI_ENABLED or not settings.OPENAI_API_KEY:
        pytest.skip("AI disabled or no API key")

    result = await check_openai_connection()
    assert result is True


@pytest.mark.asyncio
async def test_llm_basic_response():
    """Verifica que el LLM responde correctamente."""
    from app.core.ai import get_llm
    from app.core.config import settings

    if not settings.AI_ENABLED or not settings.OPENAI_API_KEY:
        pytest.skip("AI disabled or no API key")

    llm = get_llm()
    response = llm.invoke("Responde solo con 'ok'")
    assert response.content is not None
    assert len(response.content) > 0
