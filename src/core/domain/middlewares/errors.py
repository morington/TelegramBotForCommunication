from typing import Any, Awaitable, Callable

import structlog
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src import Loggers
from src.core.domain.errors.default import UnexpectedErrorInBotOperation

logger: structlog.BoundLogger = structlog.getLogger(Loggers.main.name)


class ErrorMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # try:
        #     result = await handler(event, data)
        #     return result
        # except Exception as err:
        #     raise UnexpectedErrorInBotOperation(logger) from err

        result = await handler(event, data)
        return result