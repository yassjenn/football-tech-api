from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_confirmation_token
from app.modules.attendance.models import Attendance, AttendanceStatus
from app.modules.convocations.models import Convocation
from app.modules.convocations.schemas import ConvocationCreateRequest
from app.modules.players.models import Player
from app.modules.training.models import Session, SessionStatus


class ConvocationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_convocation(
        self,
        data: ConvocationCreateRequest,
        organization_id: int,
    ) -> tuple[Convocation, list[Attendance]]:
        """
        Crea una convocatoria para una sesión y genera registros
        de asistencia con token único para cada jugador convocado.
        Verifica que la sesión pertenece a la organización y que
        todos los jugadores pertenecen a la organización.
        """
        # Verifica que la sesión existe y pertenece a la organización
        session_result = await self.db.execute(
            select(Session).where(
                Session.id == data.session_id,
                Session.organization_id == organization_id,
            )
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")

        if session.status != SessionStatus.DRAFT:
            raise ValueError("Session is not in DRAFT status")

        # Verifica que no existe ya una convocatoria para esta sesión
        existing = await self.db.execute(
            select(Convocation).where(Convocation.session_id == data.session_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Convocation already exists for this session")

        # Verifica que la fecha límite es futura
        now = datetime.now(UTC)
        deadline = data.confirmation_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=UTC)
        if deadline <= now:
            raise ValueError("Confirmation deadline must be in the future")

        # Verifica que todos los jugadores pertenecen a la organización
        players_result = await self.db.execute(
            select(Player).where(
                Player.id.in_(data.player_ids),
                Player.organization_id == organization_id,
                Player.is_active == True,  # noqa: E712
            )
        )
        players = list(players_result.scalars().all())
        if len(players) != len(data.player_ids):
            raise ValueError("Some players not found or inactive in organization")

        # Crea la convocatoria
        convocation = Convocation(
            session_id=data.session_id,
            confirmation_deadline=deadline,
            is_active=True,
        )
        self.db.add(convocation)
        await self.db.flush()

        # Crea registro de asistencia con token único para cada jugador
        attendances = []
        for player in players:
            attendance = Attendance(
                convocation_id=convocation.id,
                player_id=player.id,
                confirmation_token=generate_confirmation_token(),
                status=AttendanceStatus.PENDING,
                feedback_generated_by_ai=False,
            )
            self.db.add(attendance)
            attendances.append(attendance)

        await self.db.commit()
        await self.db.refresh(convocation)

        # Importación local para evitar circular imports
        from app.core.email import send_convocation_email
        from app.modules.organizations.models import Organization

        org_result = await self.db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        organization = org_result.scalar_one()

        session_date_str = session.session_date.strftime("%d/%m/%Y")
        deadline_str = deadline.strftime("%d/%m/%Y %H:%M")

        # Envía email a cada jugador convocado con el token de confirmación
        for player, attendance in zip(players, attendances, strict=True):
            await self.db.refresh(attendance)

            # Determina si enviar al guardian o al jugador
            if player.is_minor:
                # Obtiene los guardians del jugador
                from app.modules.players.models import GuardianPlayer
                from app.modules.users.models import GuardianProfile, User

                guardians_result = await self.db.execute(
                    select(User, GuardianProfile)
                    .join(GuardianProfile, GuardianProfile.user_id == User.id)
                    .join(
                        GuardianPlayer, GuardianPlayer.guardian_id == GuardianProfile.id
                    )
                    .where(GuardianPlayer.player_id == player.id)
                )
                guardians = list(guardians_result.all())

                if guardians:
                    for guardian_user, _ in guardians:
                        await send_convocation_email(
                            to_email=guardian_user.email,
                            to_name=guardian_user.full_name,
                            player_name=player.full_name,
                            organization_name=organization.name,
                            session_title=session.title,
                            session_date=session_date_str,
                            duration_minutes=session.duration_minutes,
                            level=session.level.value,
                            age_group=session.age_group,
                            deadline=deadline_str,
                            confirmation_token=attendance.confirmation_token,
                            is_guardian=True,
                        )
                else:
                    # Menor sin guardian — enviar al email del jugador
                    await send_convocation_email(
                        to_email=player.email,
                        to_name=player.full_name,
                        player_name=player.full_name,
                        organization_name=organization.name,
                        session_title=session.title,
                        session_date=session_date_str,
                        duration_minutes=session.duration_minutes,
                        level=session.level.value,
                        age_group=session.age_group,
                        deadline=deadline_str,
                        confirmation_token=attendance.confirmation_token,
                        is_guardian=False,
                    )
            else:
                await send_convocation_email(
                    to_email=player.email,
                    to_name=player.full_name,
                    player_name=player.full_name,
                    organization_name=organization.name,
                    session_title=session.title,
                    session_date=session_date_str,
                    duration_minutes=session.duration_minutes,
                    level=session.level.value,
                    age_group=session.age_group,
                    deadline=deadline_str,
                    confirmation_token=attendance.confirmation_token,
                    is_guardian=False,
                )

        return convocation, attendances

    async def get_convocation_by_id(
        self,
        convocation_id: int,
        organization_id: int,
    ) -> Convocation | None:
        """Obtiene una convocatoria verificando que pertenece a la organización."""
        result = await self.db.execute(
            select(Convocation)
            .join(Session, Session.id == Convocation.session_id)
            .where(
                Convocation.id == convocation_id,
                Session.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_convocations(
        self,
        organization_id: int,
    ) -> list[Convocation]:
        """Lista todas las convocatorias de la organización."""
        result = await self.db.execute(
            select(Convocation)
            .join(Session, Session.id == Convocation.session_id)
            .where(Session.organization_id == organization_id)
            .order_by(Convocation.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_convocation_attendances(
        self,
        convocation_id: int,
        organization_id: int,
    ) -> list[tuple[Attendance, Player]]:
        """
        Obtiene las asistencias de una convocatoria con datos del jugador.
        Útil para el dashboard del admin — ver quién confirmó y quién no.
        """
        convocation = await self.get_convocation_by_id(convocation_id, organization_id)
        if not convocation:
            raise ValueError("Convocation not found")

        result = await self.db.execute(
            select(Attendance, Player)
            .join(Player, Player.id == Attendance.player_id)
            .where(Attendance.convocation_id == convocation_id)
            .order_by(Player.full_name)
        )
        return list(result.all())

    async def get_confirmed_players(
        self,
        convocation_id: int,
        organization_id: int,
    ) -> list[Player]:
        """
        Obtiene solo los jugadores confirmados de una convocatoria.
        Se usa para asignar la sesión al entrenador con los jugadores confirmados.
        """
        convocation = await self.get_convocation_by_id(convocation_id, organization_id)
        if not convocation:
            raise ValueError("Convocation not found")

        result = await self.db.execute(
            select(Player)
            .join(Attendance, Attendance.player_id == Player.id)
            .where(
                Attendance.convocation_id == convocation_id,
                Attendance.status == AttendanceStatus.CONFIRMED,
            )
        )
        return list(result.scalars().all())

    async def cancel_convocation(
        self,
        convocation_id: int,
        organization_id: int,
    ) -> Convocation:
        """Cancela una convocatoria marcándola como inactiva."""
        convocation = await self.get_convocation_by_id(convocation_id, organization_id)
        if not convocation:
            raise ValueError("Convocation not found")

        convocation.is_active = False
        await self.db.commit()
        await self.db.refresh(convocation)
        return convocation

    async def _build_summary(self, convocation: Convocation) -> dict:
        """Calcula el resumen de estados de una convocatoria."""
        result = await self.db.execute(
            select(Attendance).where(Attendance.convocation_id == convocation.id)
        )
        attendances = list(result.scalars().all())
        return {
            "total_players": len(attendances),
            "confirmed": sum(
                1 for a in attendances if a.status == AttendanceStatus.CONFIRMED
            ),
            "rejected": sum(
                1 for a in attendances if a.status == AttendanceStatus.REJECTED
            ),
            "pending": sum(
                1 for a in attendances if a.status == AttendanceStatus.PENDING
            ),
            "expired": sum(
                1 for a in attendances if a.status == AttendanceStatus.EXPIRED
            ),
        }
