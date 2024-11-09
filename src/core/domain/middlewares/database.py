from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from src.infrastructure.repository.postgresql_controller.query import Query


class SessionMiddleware(BaseMiddleware):
    def __init__(self, engine: AsyncEngine):
        super().__init__()
        self.engine = engine

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with AsyncSession(self.engine) as session:
            data["query"] = Query(session)
            async with session.begin():
                result = await handler(event, data)
                return result
