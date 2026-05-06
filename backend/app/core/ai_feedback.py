from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from app.core.ai import get_llm
from app.core.config import settings

SYSTEM_PROMPT = """Eres un entrenador de fútbol profesional con experiencia en 
desarrollo de jugadores. Generas feedback personalizado, constructivo y motivador 
basado en las puntuaciones de rendimiento de los jugadores.

Responde SIEMPRE en español. El feedback debe ser:
- Personal y directo (dirigido al jugador)
- Constructivo — señala puntos de mejora sin desmotivar
- Específico — basado en las puntuaciones reales
- Breve — máximo 3 párrafos
- Motivador — termina con un mensaje positivo"""


def _build_feedback_prompt(
    player_name: str,
    session_title: str,
    technique_score: int,
    physical_score: int,
    attitude_score: int,
    level: str,
    age_group: str | None,
) -> str:
    avg = round((technique_score + physical_score + attitude_score) / 3, 1)
    age_str = f"Categoría: {age_group}." if age_group else ""

    return f"""Genera feedback personalizado para el siguiente jugador:

- Jugador: {player_name}
- Sesión: {session_title}
- Nivel del equipo: {level}
- {age_str}

Puntuaciones (escala 1-10):
- Técnica: {technique_score}/10
- Físico: {physical_score}/10
- Actitud: {attitude_score}/10
- Media: {avg}/10

Genera un feedback constructivo y motivador de máximo 3 párrafos dirigido 
directamente al jugador. Menciona sus puntos fuertes, áreas de mejora y 
termina con un mensaje motivador."""


async def generate_player_feedback(
    player_name: str,
    session_title: str,
    technique_score: int,
    physical_score: int,
    attitude_score: int,
    level: str,
    age_group: str | None = None,
) -> str:
    """
    Genera feedback personalizado para un jugador usando IA.
    Si AI_ENABLED=False devuelve feedback de ejemplo sin llamar a la API.
    """
    if not settings.AI_ENABLED or not settings.OPENAI_API_KEY:
        logger.info("AI disabled — returning placeholder feedback")
        return _placeholder_feedback(
            player_name, technique_score, physical_score, attitude_score
        )

    try:
        llm = get_llm()
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=_build_feedback_prompt(
                    player_name=player_name,
                    session_title=session_title,
                    technique_score=technique_score,
                    physical_score=physical_score,
                    attitude_score=attitude_score,
                    level=level,
                    age_group=age_group,
                )
            ),
        ]
        logger.info(f"Generating feedback for player: {player_name}")
        response = llm.invoke(messages)
        logger.info("Feedback generated successfully")
        return response.content
    except Exception as e:
        logger.error(f"Failed to generate feedback: {e}")
        raise ValueError(f"AI feedback generation failed: {e}") from e


def _placeholder_feedback(
    player_name: str,
    technique_score: int,
    physical_score: int,
    attitude_score: int,
) -> str:
    """Feedback de ejemplo cuando AI está desactivada — útil en tests."""
    avg = round((technique_score + physical_score + attitude_score) / 3, 1)
    return f"""{player_name}, has completado la sesión con una nota media de {avg}/10.

Tu técnica ({technique_score}/10) y tu condición física ({physical_score}/10) 
muestran tu nivel actual. Tu actitud ({attitude_score}/10) es clave para seguir mejorando.

¡Sigue trabajando duro y los resultados llegarán!"""
