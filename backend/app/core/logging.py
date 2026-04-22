import sys

from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    logger.remove()  # elimina el handler por defecto

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "{message}"
    )

    # Handler consola
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True,
    )

    # Handler archivo JSON (para Loki)
    logger.add(
        "logs/app.log",
        format="{time} {level} {name} {message}",
        level=settings.LOG_LEVEL,
        rotation="10 MB",
        retention="7 days",
        serialize=True,  # formato JSON
    )

    logger.info(
        f"Logging configured | env={settings.ENVIRONMENT} | level={settings.LOG_LEVEL}"
    )