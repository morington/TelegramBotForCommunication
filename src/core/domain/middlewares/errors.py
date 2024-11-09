import hashlib
import traceback
from datetime import datetime
from typing import Any, Awaitable, Callable

import structlog
from aiogram import BaseMiddleware, Bot
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import TelegramObject
from redis.asyncio import Redis

from src.core.domain.errors.default import UnexpectedErrorInBotOperation

logger: structlog.BoundLogger = structlog.getLogger("TelegramBot")


class ErrorMiddleware(BaseMiddleware):
    def __init__(self, admin: int, base_url: str) -> None:
        self.admin = admin
        self.base_url = base_url

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        bot: Bot = data.get('bot')
        fsm_storage: RedisStorage = data.get('fsm_storage')
        redis: Redis = fsm_storage.redis

        try:
            result = await handler(event, data)
            return result
        except Exception as err:
            log_traceback: str = traceback.format_exc()
            name_error: str = err.__class__.__name__
            dt: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            link: str = hashlib.md5(f"{name_error}{dt}".encode("utf-8")).hexdigest()
            await redis.set(link, log_traceback)
            await bot.send_message(self.admin, text=f"⚠️ <b>Получена ошибка!</b>\n\nСсылка: {self.base_url}/errors?id={link}\n<b>{dt}</b>")

            raise UnexpectedErrorInBotOperation(logger) from err
