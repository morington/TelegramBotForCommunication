import asyncio
from logging.config import fileConfig

import structlog
from alembic import context
from pydantic import ValidationError
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from src import Settings
from src.infrastructure.configuration.dynaconf_controller.main import Config
from src.infrastructure.repository.models import Base

logger: structlog.BoundLogger = structlog.get_logger("Alembic")

config = context.config
target_metadata = Base.metadata

# Схемы, с которыми будет работать Alembic
SCHEMAS = ["analytics", "usersystem", "public"]
VERSION_TABLE_SCHEMA = "public"

# Настройка логирования Alembic
if config.attributes.get("configure_logger", True) and config.config_file_name:
    fileConfig(config.config_file_name)

# Загрузка конфигурации из dynaconf
config_loader = Config(env="DEV", url_templates={"postgresql": "postgresql+asyncpg"})
try:
    settings = Settings(**config_loader.raw)
except ValidationError as e:
    print("Ошибка конфигурации:\n")
    for error in e.errors():
        loc = ".".join(str(x) for x in error['loc'])
        msg = error['msg']
        print(f"  - {loc}: {msg}")
    raise SystemExit(1)

# Проверка на пустой или не заданный URL
if not settings.postgresql_url or not settings.postgresql_url.strip():
    raise RuntimeError("DATABASE_URL is not set or empty")

config.set_main_option("sqlalchemy.url", settings.postgresql_url)
logger.debug("PostgreSQL configuration loaded", url=settings.postgresql_url)


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
        include_schemas=True,
        version_table_schema=VERSION_TABLE_SCHEMA,
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
