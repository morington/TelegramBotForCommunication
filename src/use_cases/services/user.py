from typing import Optional

from src.core.domain.entities import UserEntity
from src.core.domain.interfaces.database.user import AbstractUserRepo


class UserService:
    def __init__(self, repo: AbstractUserRepo) -> None:
        self.repo = repo

    async def get_user(self, user_telegram_id: int) -> Optional[UserEntity]:
        return await self.repo.get_user_by_telegram_id(user_telegram_id=user_telegram_id)

    async def add_user(self, user: UserEntity) -> UserEntity:
        return await self.repo.add_user(user=user)
