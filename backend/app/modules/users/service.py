from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.modules.organizations.models import Organization
from app.modules.users.models import AdminProfile, CoachProfile, User, UserRole
from app.modules.users.schemas import (
    CoachCreateRequest,
    CoachUpdateRequest,
    LoginRequest,
    RegisterRequest,
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: RegisterRequest) -> User:
        """
        Registra un nuevo usuario (Admin o Coach).
        Si el rol es Admin, crea también la organización y el perfil.
        Si el rol es Coach, solo crea el perfil de coach.
        """
        # Verifica que el email no esté ya registrado
        existing = await self.db.execute(select(User).where(User.email == data.email))
        if existing.scalar_one_or_none():
            raise ValueError("Email already registered")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.flush()  # genera el user.id sin hacer commit

        if data.role == UserRole.ADMIN:
            await self._create_admin(user, data)
        elif data.role == UserRole.COACH:
            await self._create_coach(user)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def _create_admin(self, user: User, data: RegisterRequest) -> None:
        """Crea la organización y el perfil de admin."""
        org_name = data.organization_name or f"{user.full_name}'s Organization"
        slug = org_name.lower().replace(" ", "-")

        organization = Organization(
            name=org_name,
            slug=slug,
            is_active=True,
        )
        self.db.add(organization)
        await self.db.flush()

        user.organization_id = organization.id
        admin_profile = AdminProfile(
            user_id=user.id,
            organization_id=organization.id,
            is_active=True,
        )
        self.db.add(admin_profile)

    async def _create_coach(self, user: User) -> None:
        """Crea el perfil de coach sin organización — el admin la asigna después."""
        coach_profile = CoachProfile(
            user_id=user.id,
            organization_id=None,
            is_active=True,
        )
        self.db.add(coach_profile)

    async def login(self, data: LoginRequest) -> tuple[User, str]:
        """
        Autentica un usuario y genera un JWT.
        Devuelve el usuario y el token.
        """
        result = await self.db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            raise ValueError("Invalid credentials")

        if not user.is_active:
            raise ValueError("User is inactive")

        token = create_access_token(
            subject=str(user.id),
            role=user.role.value,
        )
        return user, token

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Obtiene un usuario por su ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


class CoachService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_coach(
        self,
        data: CoachCreateRequest,
        organization_id: int,
    ) -> tuple[User, CoachProfile]:
        """
        Crea un nuevo entrenador en la organización del admin.
        Crea el User con rol COACH y su CoachProfile vinculado.
        """
        # Verifica email único
        existing = await self.db.execute(select(User).where(User.email == data.email))
        if existing.scalar_one_or_none():
            raise ValueError("Email already registered")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=UserRole.COACH,
            is_active=True,
            is_verified=True,  # el admin crea la cuenta, no necesita verificación
            organization_id=organization_id,
        )
        self.db.add(user)
        await self.db.flush()

        coach_profile = CoachProfile(
            user_id=user.id,
            organization_id=organization_id,
            phone=data.phone,
            bio=data.bio,
            is_active=True,
        )
        self.db.add(coach_profile)
        await self.db.commit()
        await self.db.refresh(user)
        await self.db.refresh(coach_profile)
        return user, coach_profile

    async def get_coaches(
        self,
        organization_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[tuple[User, CoachProfile]], int]:
        """
        Lista todos los entrenadores de una organización con paginación.
        Devuelve los items y el total para el frontend.
        """
        base_query = (
            select(User, CoachProfile)
            .join(CoachProfile, CoachProfile.user_id == User.id)
            .where(CoachProfile.organization_id == organization_id)
        )

        # Total para paginación
        count_result = await self.db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar_one()

        # Items paginados
        result = await self.db.execute(
            base_query.order_by(User.full_name)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = result.all()
        return items, total

    async def get_coach_by_id(
        self,
        coach_id: int,
        organization_id: int,
    ) -> tuple[User, CoachProfile] | None:
        """Obtiene un entrenador por ID verificando que pertenece a la organización."""
        result = await self.db.execute(
            select(User, CoachProfile)
            .join(CoachProfile, CoachProfile.user_id == User.id)
            .where(
                CoachProfile.id == coach_id,
                CoachProfile.organization_id == organization_id,
            )
        )
        return result.one_or_none()

    async def update_coach(
        self,
        coach_id: int,
        organization_id: int,
        data: CoachUpdateRequest,
    ) -> tuple[User, CoachProfile]:
        """
        Actualiza datos del entrenador.
        Solo actualiza los campos que vienen en el request (PATCH semántico).
        """
        row = await self.get_coach_by_id(coach_id, organization_id)
        if not row:
            raise ValueError("Coach not found")

        user, coach_profile = row

        if data.full_name is not None:
            user.full_name = data.full_name
        if data.phone is not None:
            coach_profile.phone = data.phone
        if data.bio is not None:
            coach_profile.bio = data.bio
        if data.is_active is not None:
            user.is_active = data.is_active
            coach_profile.is_active = data.is_active

        await self.db.commit()
        await self.db.refresh(user)
        await self.db.refresh(coach_profile)
        return user, coach_profile

    async def deactivate_coach(
        self,
        coach_id: int,
        organization_id: int,
    ) -> tuple[User, CoachProfile]:
        """
        Desactiva un entrenador — no lo elimina.
        El borrado lógico preserva el historial de sesiones.
        """
        row = await self.get_coach_by_id(coach_id, organization_id)
        if not row:
            raise ValueError("Coach not found")

        user, coach_profile = row
        user.is_active = False
        coach_profile.is_active = False

        await self.db.commit()
        await self.db.refresh(user)
        await self.db.refresh(coach_profile)
        return user, coach_profile
