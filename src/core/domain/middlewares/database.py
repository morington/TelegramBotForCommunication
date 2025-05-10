from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from src.infrastructure.repository.queries.profile import FreelancerProfileQuery
from src.infrastructure.repository.queries.user import UserQuery
from src.use_cases.services.profile import FreelancerProfileService
from src.use_cases.services.user import UserService


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

            data["user_query"] = UserService(repo=UserQuery(session=session))
            data["freelancer_profile_query"] = FreelancerProfileService(repo=FreelancerProfileQuery(session=session))

            async with session.begin():
                result = await handler(event, data)
                return result
