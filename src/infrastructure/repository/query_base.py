from sqlalchemy.ext.asyncio import AsyncSession


class Query:
    """Класс для запросов"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
