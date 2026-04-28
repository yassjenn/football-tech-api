import asyncio
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import create_async_engine

import app.modules.attendance.models  # noqa: F401
import app.modules.convocations.models  # noqa: F401
import app.modules.organizations.models  # noqa: F401
import app.modules.players.models  # noqa: F401
import app.modules.training.models  # noqa: F401

# Importamos todos los módulos para que Alembic detecte los modelos
# Si no se importan aquí, Alembic no genera las migraciones correctamente
import app.modules.users.models  # noqa: F401
from alembic import context
from app.core.config import settings
from app.core.database import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Base.metadata contiene todos los modelos importados arriba
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Modo offline: genera el SQL sin conectarse a la base de datos.
    Útil para revisar los cambios antes de aplicarlos.
    """
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # detecta cambios de tipo en columnas
        compare_server_default=True,  # detecta cambios en valores por defecto
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Modo online: se conecta a la base de datos y aplica las migraciones.
    Usamos el engine async igual que en la aplicación.
    """
    connectable = create_async_engine(settings.DATABASE_URL)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
