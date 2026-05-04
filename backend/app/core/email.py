from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jinja2 import Environment, FileSystemLoader
from loguru import logger

from app.core.config import settings

# Configuración de FastMail
mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=bool(settings.MAIL_USERNAME),
    VALIDATE_CERTS=True,
)

# Jinja2 para renderizar plantillas
templates_path = Path(__file__).parent.parent / "templates" / "email"
jinja_env = Environment(loader=FileSystemLoader(str(templates_path)))


async def send_convocation_email(
    to_email: str,
    to_name: str,
    player_name: str,
    organization_name: str,
    session_title: str,
    session_date: str,
    duration_minutes: int,
    level: str,
    age_group: str | None,
    deadline: str,
    confirmation_token: str,
    is_guardian: bool = False,
) -> bool:
    """
    Envía el email de convocatoria con el enlace de confirmación.
    Si MAIL_ENABLED=False (desarrollo), solo loguea el enlace sin enviar.
    Devuelve True si el email se envió correctamente.
    """
    confirm_url = f"{settings.FRONTEND_URL}/confirm/{confirmation_token}?action=confirm"
    reject_url = f"{settings.FRONTEND_URL}/confirm/{confirmation_token}?action=reject"

    template_name = "convocation_guardian.html" if is_guardian else "convocation.html"
    template = jinja_env.get_template(template_name)

    context = {
        "guardian_name": to_name if is_guardian else None,
        "player_name": player_name,
        "organization_name": organization_name,
        "session_title": session_title,
        "session_date": session_date,
        "duration_minutes": duration_minutes,
        "level": level,
        "age_group": age_group,
        "deadline": deadline,
        "confirm_url": confirm_url,
        "reject_url": reject_url,
    }

    html_content = template.render(**context)

    if not settings.MAIL_ENABLED:
        # En desarrollo mostramos el enlace en los logs
        logger.info(
            f"[EMAIL DISABLED] Convocation email for {to_email} | "
            f"Player: {player_name} | "
            f"Confirm: {confirm_url} | "
            f"Reject: {reject_url}"
        )
        return True

    try:
        message = MessageSchema(
            subject=f"Convocatoria: {session_title}",
            recipients=[to_email],
            body=html_content,
            subtype=MessageType.html,
        )
        fm = FastMail(mail_config)
        await fm.send_message(message)
        logger.info(f"Convocation email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False
