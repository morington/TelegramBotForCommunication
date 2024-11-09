import asyncio

import structlog
from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command

from src.core.application.telegrambot import TelegramBotManager
from src.core.domain.errors.default import UnexpectedErrorInBotStartup
from src.infrastructure.improved_logging.main import SetupLogger, LoggerReg

logger: structlog.BoundLogger = structlog.getLogger("Main")
SetupLogger(
    developer_mode=True,
    name_registration=[
        LoggerReg("Alembic", level=LoggerReg.Level.INFO),
        LoggerReg("Main", level=LoggerReg.Level.DEBUG),
        LoggerReg("TelegramBot", level=LoggerReg.Level.DEBUG),
        LoggerReg("AccessFilter", level=LoggerReg.Level.INFO),
        LoggerReg("DatabaseQuery", level=LoggerReg.Level.DEBUG),
    ],
)


if __name__ == "__main__":
    alembic_config = AlembicConfig(file_="alembic.ini", attributes={"configure_logger": False})
    alembic_command.upgrade(alembic_config, "head")
    logger.info("Database migrations updated")

    manager = TelegramBotManager()

    try:
        manager.start()
    except KeyboardInterrupt:
        logger.info("Прервано пользователем")
        manager.stop()
    except Exception as err:
        raise UnexpectedErrorInBotStartup(logger) from err
