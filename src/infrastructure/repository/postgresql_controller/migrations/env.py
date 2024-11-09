import asyncio
from logging.config import fileConfig
from pathlib import Path

import structlog
from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from src.project import BASE_PATH, MODE
from src.infrastructure.repository.postgresql_controller.models import Base
from src.infrastructure.configuration.dynaconf_controller.main import ConfigurationParserFromDynaconf

logger: structlog.BoundLogger = structlog.get_logger("Alembic")

config = context.config
target_metadata = Base.metadata

if config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name)

settings_files: list[Path] = [Path("config/settings.yml"), Path("config/.secrets.yml")]
configuration = ConfigurationParserFromDynaconf(*settings_files, environment=MODE, base_dir=BASE_PATH)

logger.debug("Database__PostgreSQL configuration", url=configuration.data.get("database_url"))
config.set_main_option("sqlalchemy.url", configuration.data.get("database_url"),)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
