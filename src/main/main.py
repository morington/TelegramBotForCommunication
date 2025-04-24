import asyncio

import structlog
from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command

from src import Loggers
from src.core.application import TelegramBotManager
from src.core.domain.errors.default import UnexpectedErrorInBotStartup

logger: structlog.BoundLogger = structlog.getLogger(Loggers.main.name)


async def main():
    manager = TelegramBotManager()

    try:
        await manager.start_polling()
    except Exception as err:
        raise UnexpectedErrorInBotStartup(logger) from err


if __name__ == "__main__":
    Loggers(developer_mode=True)

    alembic_config = AlembicConfig(file_="alembic.ini", attributes={"configure_logger": False})
    alembic_command.upgrade(alembic_config, "head")
    logger.info("Database migrations updated")

    asyncio.run(main())
