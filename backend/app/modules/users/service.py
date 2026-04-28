from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.modules.organizations.models import Organization
from app.modules.users.models import AdminProfile, CoachProfile, User, UserRole
from app.modules.users.schemas import LoginRequest, RegisterRequest


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
        """Crea el perfil de coach."""
        coach_profile = CoachProfile(
            user_id=user.id,
            organization_id=user.organization_id,
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
