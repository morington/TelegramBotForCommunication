from src.config.lmuwj4 import Settings
from src.infrastructure.logger.main import InitLoggers, LoggerReg


class Loggers(InitLoggers):
    _ALEMBIC = LoggerReg(name="Alembic", level=LoggerReg.Level.DEBUG)

    main = LoggerReg(name="MAIN", level=LoggerReg.Level.DEBUG)


__all__ = ["Settings", "Loggers"]
