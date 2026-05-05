from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.training.models import Session, SessionStatus
from app.modules.training.schemas import SessionCreateRequest, SessionUpdateRequest


class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        data: SessionCreateRequest,
        organization_id: int,
    ) -> Session:
        """Crea una sesión en estado DRAFT."""
        session = Session(
            title=data.title,
            description=data.description,
            session_date=data.session_date,
            duration_minutes=data.duration_minutes,
            level=data.level,
            age_group=data.age_group,
            organization_id=organization_id,
            status=SessionStatus.DRAFT,
            content_generated_by_ai=False,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_sessions(
        self,
        organization_id: int,
        page: int = 1,
        page_size: int = 20,
        status: SessionStatus | None = None,
    ) -> tuple[list[Session], int]:
        """Lista sesiones de la organización con paginación y filtro por estado."""
        query = select(Session).where(Session.organization_id == organization_id)
        if status:
            query = query.where(Session.status == status)

        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await self.db.execute(
            query.order_by(Session.session_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_session_by_id(
        self,
        session_id: int,
        organization_id: int,
    ) -> Session | None:
        """Obtiene una sesión verificando que pertenece a la organización."""
        result = await self.db.execute(
            select(Session).where(
                Session.id == session_id,
                Session.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_session(
        self,
        session_id: int,
        organization_id: int,
        data: SessionUpdateRequest,
    ) -> Session:
        """Actualiza datos de la sesión — solo en estado DRAFT."""
        session = await self.get_session_by_id(session_id, organization_id)
        if not session:
            raise ValueError("Session not found")
        if session.status != SessionStatus.DRAFT:
            raise ValueError("Only DRAFT sessions can be edited")

        if data.title is not None:
            session.title = data.title
        if data.description is not None:
            session.description = data.description
        if data.session_date is not None:
            session.session_date = data.session_date
        if data.duration_minutes is not None:
            session.duration_minutes = data.duration_minutes
        if data.level is not None:
            session.level = data.level
        if data.age_group is not None:
            session.age_group = data.age_group

        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def cancel_session(
        self,
        session_id: int,
        organization_id: int,
    ) -> Session:
        """Cancela una sesión."""
        session = await self.get_session_by_id(session_id, organization_id)
        if not session:
            raise ValueError("Session not found")
        if session.status == SessionStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed session")

        session.status = SessionStatus.CANCELLED
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def assign_coach(
        self,
        session_id: int,
        organization_id: int,
        coach_id: int,
    ) -> Session:
        """
        Admin asigna un entrenador a la sesión.
        La sesión pasa de DRAFT a ASSIGNED.
        Verifica que el coach pertenece a la organización.
        """
        from app.modules.users.models import CoachProfile

        session = await self.get_session_by_id(session_id, organization_id)
        if not session:
            raise ValueError("Session not found")
        if session.status != SessionStatus.DRAFT:
            raise ValueError("Only DRAFT sessions can be assigned")

        coach_result = await self.db.execute(
            select(CoachProfile).where(
                CoachProfile.id == coach_id,
                CoachProfile.organization_id == organization_id,
                CoachProfile.is_active == True,  # noqa: E712
            )
        )
        coach = coach_result.scalar_one_or_none()
        if not coach:
            raise ValueError("Coach not found in organization")

        session.coach_id = coach_id
        session.status = SessionStatus.ASSIGNED
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def accept_session(
        self,
        session_id: int,
        coach_profile_id: int,
    ) -> Session:
        """
        El entrenador acepta la sesión asignada.
        La sesión pasa de ASSIGNED a ACCEPTED.
        """
        result = await self.db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")
        if session.coach_id != coach_profile_id:
            raise ValueError("You are not assigned to this session")
        if session.status != SessionStatus.ASSIGNED:
            raise ValueError("Session is not in ASSIGNED status")

        session.status = SessionStatus.ACCEPTED
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def start_session(
        self,
        session_id: int,
        coach_profile_id: int,
    ) -> Session:
        """
        El entrenador marca la sesión como en curso.
        La sesión pasa de ACCEPTED a IN_PROGRESS.
        """
        result = await self.db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")
        if session.coach_id != coach_profile_id:
            raise ValueError("You are not assigned to this session")
        if session.status != SessionStatus.ACCEPTED:
            raise ValueError("Session must be ACCEPTED before starting")

        session.status = SessionStatus.IN_PROGRESS
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def complete_session(
        self,
        session_id: int,
        coach_profile_id: int,
    ) -> Session:
        """
        El entrenador completa la sesión.
        La sesión pasa de IN_PROGRESS a COMPLETED.
        """
        result = await self.db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")
        if session.coach_id != coach_profile_id:
            raise ValueError("You are not assigned to this session")
        if session.status != SessionStatus.IN_PROGRESS:
            raise ValueError("Session must be IN_PROGRESS before completing")

        session.status = SessionStatus.COMPLETED
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def add_content(
        self,
        session_id: int,
        organization_id: int,
        content: str,
        generated_by_ai: bool = False,
    ) -> Session:
        """
        Añade contenido de ejercicios a la sesión.
        Accesible por admin y coach asignado.
        """
        session = await self.get_session_by_id(session_id, organization_id)
        if not session:
            raise ValueError("Session not found")
        if session.status == SessionStatus.COMPLETED:
            raise ValueError("Cannot edit a completed session")
        if session.status == SessionStatus.CANCELLED:
            raise ValueError("Cannot edit a cancelled session")

        session.content = content
        session.content_generated_by_ai = generated_by_ai
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_coach_profile_id(
        self,
        user_id: int,
        organization_id: int,
    ) -> int:
        """Helper — obtiene el CoachProfile.id a partir del User.id."""
        from app.modules.users.models import CoachProfile

        result = await self.db.execute(
            select(CoachProfile).where(
                CoachProfile.user_id == user_id,
                CoachProfile.organization_id == organization_id,
            )
        )
        coach = result.scalar_one_or_none()
        if not coach:
            raise ValueError("Coach profile not found")
        return coach.id
