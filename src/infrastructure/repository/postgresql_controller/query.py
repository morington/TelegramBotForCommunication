import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger: structlog.BoundLogger = structlog.get_logger("DatabaseQuery")


class Query:
    """Класс для запросов"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
