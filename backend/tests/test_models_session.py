from datetime import UTC, date, datetime

from app.modules.attendance.models import Attendance, AttendanceStatus, ConfirmedBy
from app.modules.convocations.models import Convocation
from app.modules.training.models import Session, SessionLevel, SessionStatus


def test_session_model_defaults():
    session = Session(
        title="Sesión técnica",
        session_date=date(2026, 5, 1),
        organization_id=1,
        status=SessionStatus.DRAFT,
        level=SessionLevel.INTERMEDIATE,
        content_generated_by_ai=False,
    )
    assert session.status == SessionStatus.DRAFT
    assert session.coach_id is None


def test_session_status_transitions():
    assert SessionStatus.DRAFT == "draft"
    assert SessionStatus.ASSIGNED == "assigned"
    assert SessionStatus.COMPLETED == "completed"


def test_convocation_model():
    deadline = datetime(2026, 4, 30, 23, 59, tzinfo=UTC)
    conv = Convocation(session_id=1, confirmation_deadline=deadline, is_active=True)
    assert conv.session_id == 1
    assert conv.is_active is True


def test_attendance_model_defaults():
    attendance = Attendance(
        convocation_id=1,
        player_id=1,
        confirmation_token="unique-token-abc123",
        status=AttendanceStatus.PENDING,
        feedback_generated_by_ai=False,
    )
    assert attendance.status == AttendanceStatus.PENDING
    assert attendance.confirmed_by is None


def test_attendance_confirmed_by_admin():
    attendance = Attendance(
        convocation_id=1,
        player_id=1,
        confirmation_token="token-admin",
        status=AttendanceStatus.CONFIRMED,
        confirmed_by=ConfirmedBy.ADMIN,
        feedback_generated_by_ai=False,
    )
    assert attendance.confirmed_by == ConfirmedBy.ADMIN


def test_attendance_confirmed_by_guardian():
    attendance = Attendance(
        convocation_id=1,
        player_id=1,
        confirmation_token="token-guardian",
        status=AttendanceStatus.CONFIRMED,
        confirmed_by=ConfirmedBy.GUARDIAN,
        feedback_generated_by_ai=False,
    )
    assert attendance.confirmed_by == ConfirmedBy.GUARDIAN
