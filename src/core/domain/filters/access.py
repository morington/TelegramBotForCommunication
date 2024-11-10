from typing import Optional

import structlog
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

logger: structlog.BoundLogger = structlog.getLogger("AccessFilter")


class AccessFilter(BaseFilter):
    def __init__(self, moderators: list[int], admin: int) -> None:
        self.moderators = moderators
        self.admin = admin

    async def __call__(self, update: Message | CallbackQuery) -> bool:
        meta: Optional[str] = None
        user_id: int = update.from_user.id
        valid_user: bool = user_id in self.moderators or user_id == self.admin

        if isinstance(update, Message):
            meta = update.text
        elif isinstance(update, CallbackQuery):
            meta = update.data

        if not valid_user:
            await logger.ainfo("Unauthorized access requested", type=type(update), user_id=user_id, meta=meta)

        return valid_user
