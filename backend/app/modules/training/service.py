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
