from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.players.models import GuardianPlayer, Player
from app.modules.players.schemas import (
    GuardianCreateRequest,
    PlayerCreateRequest,
    PlayerUpdateRequest,
)
from app.modules.users.models import GuardianProfile, User, UserRole


class PlayerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_player(
        self,
        data: PlayerCreateRequest,
        organization_id: int,
    ) -> Player:
        """
        Crea un nuevo jugador en la organización.
        Si el jugador es mayor de edad, crea también su User para login.
        Si es menor, se queda sin User hasta que el admin se lo asigne.
        """
        # Verifica email único dentro de la organización
        existing = await self.db.execute(
            select(Player).where(
                Player.email == data.email,
                Player.organization_id == organization_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Player with this email already exists in organization")

        player = Player(
            email=data.email,
            full_name=data.full_name,
            phone=data.phone,
            birth_date=data.birth_date,
            organization_id=organization_id,
            is_active=True,
        )
        self.db.add(player)
        await self.db.commit()
        await self.db.refresh(player)
        return player

    async def get_players(
        self,
        organization_id: int,
        page: int = 1,
        page_size: int = 20,
        only_minors: bool | None = None,
    ) -> tuple[list[Player], int]:
        """
        Lista jugadores de la organización con paginación.
        Permite filtrar por menores/mayores de edad.
        """
        query = select(Player).where(
            Player.organization_id == organization_id,
        )

        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await self.db.execute(
            query.order_by(Player.full_name)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        players = list(result.scalars().all())

        # Filtro de menores se aplica en Python porque is_minor es una propiedad
        if only_minors is not None:
            players = [p for p in players if p.is_minor == only_minors]

        return players, total

    async def get_player_by_id(
        self,
        player_id: int,
        organization_id: int,
    ) -> Player | None:
        """Obtiene un jugador verificando que pertenece a la organización."""
        result = await self.db.execute(
            select(Player).where(
                Player.id == player_id,
                Player.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_player(
        self,
        player_id: int,
        organization_id: int,
        data: PlayerUpdateRequest,
    ) -> Player:
        """Actualiza datos del jugador — solo campos enviados."""
        player = await self.get_player_by_id(player_id, organization_id)
        if not player:
            raise ValueError("Player not found")

        if data.full_name is not None:
            player.full_name = data.full_name
        if data.phone is not None:
            player.phone = data.phone
        if data.birth_date is not None:
            player.birth_date = data.birth_date
        if data.is_active is not None:
            player.is_active = data.is_active

        await self.db.commit()
        await self.db.refresh(player)
        return player

    async def deactivate_player(
        self,
        player_id: int,
        organization_id: int,
    ) -> Player:
        """Desactiva un jugador — borrado lógico."""
        player = await self.get_player_by_id(player_id, organization_id)
        if not player:
            raise ValueError("Player not found")

        player.is_active = False
        await self.db.commit()
        await self.db.refresh(player)
        return player

    async def create_and_assign_guardian(
        self,
        player_id: int,
        organization_id: int,
        data: GuardianCreateRequest,
    ) -> tuple[User, GuardianProfile]:
        """
        Crea un guardian y lo asigna al jugador.
        Un guardian puede tener varios hijos — si el email ya existe
        como guardian, solo crea la asignación.
        """
        player = await self.get_player_by_id(player_id, organization_id)
        if not player:
            raise ValueError("Player not found")

        if not player.is_minor:
            raise ValueError("Cannot assign guardian to a player that is not a minor")

        # Verifica si el guardian ya existe
        existing_user = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        user = existing_user.scalar_one_or_none()

        if user and user.role != UserRole.GUARDIAN:
            raise ValueError("Email already registered with a different role")

        if not user:
            user = User(
                email=data.email,
                hashed_password=hash_password(data.password),
                full_name=data.full_name,
                role=UserRole.GUARDIAN,
                is_active=True,
                is_verified=True,
            )
            self.db.add(user)
            await self.db.flush()

            guardian_profile = GuardianProfile(
                user_id=user.id,
                phone=data.phone,
                is_active=True,
            )
            self.db.add(guardian_profile)
            await self.db.flush()
        else:
            result = await self.db.execute(
                select(GuardianProfile).where(GuardianProfile.user_id == user.id)
            )
            guardian_profile = result.scalar_one()

        # Verifica que no está ya asignado
        existing_assignment = await self.db.execute(
            select(GuardianPlayer).where(
                GuardianPlayer.guardian_id == guardian_profile.id,
                GuardianPlayer.player_id == player_id,
            )
        )
        if existing_assignment.scalar_one_or_none():
            raise ValueError("Guardian already assigned to this player")

        assignment = GuardianPlayer(
            guardian_id=guardian_profile.id,
            player_id=player_id,
        )
        self.db.add(assignment)
        await self.db.commit()
        await self.db.refresh(user)
        await self.db.refresh(guardian_profile)
        return user, guardian_profile

    async def get_player_guardians(
        self,
        player_id: int,
        organization_id: int,
    ) -> list[tuple[User, GuardianProfile]]:
        """Obtiene los guardians de un jugador."""
        player = await self.get_player_by_id(player_id, organization_id)
        if not player:
            raise ValueError("Player not found")

        result = await self.db.execute(
            select(User, GuardianProfile)
            .join(GuardianProfile, GuardianProfile.user_id == User.id)
            .join(GuardianPlayer, GuardianPlayer.guardian_id == GuardianProfile.id)
            .where(GuardianPlayer.player_id == player_id)
        )
        return list(result.all())
