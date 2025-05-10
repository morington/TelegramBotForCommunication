from typing import Any, Awaitable, Callable, Optional

import structlog
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User, Message, CallbackQuery

from src import Loggers
from src.core.domain.entities import UserEntity
from src.use_cases.services.user import UserService

logger = structlog.getLogger(Loggers.middlewares.name)


class EnsureUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        user_query: UserService = data.get("user_query")

        if not user_query:
            raise RuntimeError("The database should be initialized earlier")

        telegram_user: User = self.get_telegram_user(event=event)

        if not telegram_user:
            await logger.adebug(
                "Checking is required!",
                _type_update=type(event),
                _type_event=type(event.event),
                event=event.event
            )
            raise ValueError("The update has no `Message` event or `CallbackQuery`.")

        result: Optional[UserEntity] = await user_query.get_user(user_telegram_id=telegram_user.id)
        if not result:
            user_entity = UserEntity(
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                full_name=telegram_user.full_name,
                url=telegram_user.url
            )
            result: UserEntity = await user_query.add_user(user=user_entity)
            await logger.adebug("Added new user", user=result)

        data["user_entity"]: UserEntity = result
        data["user_telegram_id"]: int = result.telegram_id

        result = await handler(event, data)
        return result

    @staticmethod
    def get_telegram_user(event: Update) -> Optional[User]:
        telegram_event = event.event

        if isinstance(telegram_event, Message):
            return telegram_event.from_user
        elif isinstance(telegram_event, CallbackQuery):
            return telegram_event.from_user
        else:
            logger.debug("Unknown event", type_event=type(telegram_event))

