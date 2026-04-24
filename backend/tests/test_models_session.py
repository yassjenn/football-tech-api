from datetime import UTC, date, datetime

from app.models.attendance import Attendance, AttendanceStatus
from app.models.convocation import Convocation
from app.models.session import Session, SessionLevel, SessionStatus


def test_session_model_defaults():
    """Verifica que Session se instancia con los valores por defecto correctos."""
    session = Session(
        title="Sesión técnica",
        session_date=date(2026, 5, 1),
        organization_id=1,
        status=SessionStatus.DRAFT,
        level=SessionLevel.INTERMEDIATE,
        content_generated_by_ai=False,
    )
    assert session.title == "Sesión técnica"
    assert session.status == SessionStatus.DRAFT
    assert session.level == SessionLevel.INTERMEDIATE
    assert session.coach_id is None
    assert session.content is None


def test_session_status_transitions():
    """Verifica que los estados del enum son los esperados."""
    assert SessionStatus.DRAFT == "draft"
    assert SessionStatus.ASSIGNED == "assigned"
    assert SessionStatus.ACCEPTED == "accepted"
    assert SessionStatus.COMPLETED == "completed"
    assert SessionStatus.CANCELLED == "cancelled"


def test_convocation_model():
    """Verifica que Convocation se instancia correctamente."""
    deadline = datetime(2026, 4, 30, 23, 59, tzinfo=UTC)
    conv = Convocation(
        session_id=1,
        confirmation_deadline=deadline,
        is_active=True,
    )
    assert conv.session_id == 1
    assert conv.confirmation_deadline == deadline
    assert conv.is_active is True


def test_attendance_model_defaults():
    """Verifica que Attendance se instancia con estado PENDING por defecto."""
    attendance = Attendance(
        convocation_id=1,
        player_id=1,
        confirmation_token="unique-token-abc123",
        status=AttendanceStatus.PENDING,
        feedback_generated_by_ai=False,
    )
    assert attendance.status == AttendanceStatus.PENDING
    assert attendance.confirmation_token == "unique-token-abc123"
    assert attendance.technique_score is None
    assert attendance.feedback is None


def test_attendance_status_values():
    """Verifica que los estados de asistencia son los correctos."""
    assert AttendanceStatus.PENDING == "pending"
    assert AttendanceStatus.CONFIRMED == "confirmed"
    assert AttendanceStatus.REJECTED == "rejected"
    assert AttendanceStatus.EXPIRED == "expired"
