from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.infrastructure.natslib.client import NatsClient


class NatsClientMiddleware(BaseMiddleware):
    def __init__(
            self,
            nats_client: NatsClient
    ) -> None:
        super().__init__()
        self.nats_client = nats_client

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["nats_client"] = self.nats_client
        return await handler(event, data)
