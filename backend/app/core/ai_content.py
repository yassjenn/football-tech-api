from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from app.core.ai import get_llm
from app.core.config import settings
from app.modules.training.models import SessionLevel

SYSTEM_PROMPT = """Eres un entrenador de fútbol profesional con experiencia en diseño 
de sesiones de entrenamiento. Generas planes de entrenamiento estructurados, prácticos 
y adaptados al nivel y edad de los jugadores.

Responde SIEMPRE en español. El formato de respuesta debe ser texto estructurado con 
secciones claras: calentamiento, parte principal y vuelta a la calma. Incluye duración 
estimada para cada ejercicio. Sé específico y práctico."""


def _build_content_prompt(
    title: str,
    duration_minutes: int,
    level: SessionLevel,
    age_group: str | None,
    description: str | None,
) -> str:
    level_labels = {
        SessionLevel.BEGINNER: "principiante",
        SessionLevel.INTERMEDIATE: "intermedio",
        SessionLevel.ADVANCED: "avanzado",
    }
    level_str = level_labels.get(level, "intermedio")
    age_str = f"Categoría de edad: {age_group}." if age_group else ""
    desc_str = f"Contexto adicional: {description}." if description else ""

    return f"""Genera un plan de entrenamiento de fútbol con las siguientes características:

- Título de la sesión: {title}
- Duración total: {duration_minutes} minutos
- Nivel: {level_str}
- {age_str}
- {desc_str}

El plan debe incluir:
1. Calentamiento (10-15% del tiempo)
2. Parte principal con 2-3 ejercicios específicos
3. Vuelta a la calma (5-10% del tiempo)

Para cada ejercicio incluye: nombre, descripción, duración, objetivos y organización 
del espacio/jugadores. Sé concreto y práctico."""


async def generate_session_content(
    title: str,
    duration_minutes: int,
    level: SessionLevel,
    age_group: str | None = None,
    description: str | None = None,
) -> str:
    """
    Genera contenido de ejercicios para una sesión usando IA.
    Si AI_ENABLED=False devuelve contenido de ejemplo sin llamar a la API.
    """
    if not settings.AI_ENABLED or not settings.OPENAI_API_KEY:
        logger.info("AI disabled — returning placeholder content")
        return _placeholder_content(title, duration_minutes, level)

    try:
        llm = get_llm()
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=_build_content_prompt(
                    title, duration_minutes, level, age_group, description
                )
            ),
        ]
        logger.info(f"Generating content for session: {title} | level: {level}")
        response = llm.invoke(messages)
        logger.info("Content generated successfully")
        return response.content
    except Exception as e:
        logger.error(f"Failed to generate content: {e}")
        raise ValueError(f"AI content generation failed: {e}") from e


def _placeholder_content(
    title: str,
    duration_minutes: int,
    level: SessionLevel,
) -> str:
    """Contenido de ejemplo cuando AI está desactivada — útil en tests."""
    return f"""# {title}

## Calentamiento (15 min)
- Movilidad articular: 5 min
- Rondos 4v2: 10 min

## Parte Principal ({duration_minutes - 25} min)
- Ejercicio técnico: control orientado y conducción
- Ejercicio táctico: presión y repliegue
- Partido reducido 5v5

## Vuelta a la calma (10 min)
- Estiramientos en grupo
- Reflexión de la sesión

Nivel: {level.value}
"""
