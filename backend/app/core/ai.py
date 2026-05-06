import os

from langchain_openai import ChatOpenAI
from loguru import logger

from app.core.config import settings


def get_llm() -> ChatOpenAI:
    """
    Devuelve el cliente LLM configurado con OpenAI.
    """
    if settings.LANGCHAIN_TRACING_V2 and settings.LANGCHAIN_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
        logger.info(
            f"LangSmith tracing enabled — project: {settings.LANGCHAIN_PROJECT}"
        )
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"

    return ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL,
        temperature=0.7,
    )


async def check_openai_connection() -> bool:
    """
    Verifica que la API key de OpenAI es válida.
    """
    try:
        llm = get_llm()
        response = llm.invoke("responde solo con 'ok'")
        logger.info("OpenAI connection OK")
        return bool(response.content)
    except Exception as e:
        logger.warning(f"OpenAI not available: {e}")
        return False
