import asyncio

import structlog
from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command

from src.infrastructure.improved_logging.main import SetupLogger, LoggerReg

logger: structlog.BoundLogger = structlog.getLogger("Main")
SetupLogger(
    developer_mode=True,
    name_registration=[
        LoggerReg("Alembic", level=LoggerReg.Level.INFO),
        LoggerReg("Main", level=LoggerReg.Level.DEBUG),
    ],
)


async def main() -> None:
    ...


if __name__ == "__main__":
    alembic_config = AlembicConfig(file_="alembic.ini", attributes={"configure_logger": False})
    alembic_command.upgrade(alembic_config, "head")
    logger.info("Database migrations updated")

    asyncio.run(main())
