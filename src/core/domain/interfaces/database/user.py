from abc import ABC, abstractmethod
from typing import Optional

from src.core.domain.entities import UserEntity


class AbstractUserRepo(ABC):
    @abstractmethod
    async def get_user(self, user_telegram_id: int) -> Optional[UserEntity]:
        ...

    @abstractmethod
    async def add_user(self, user: UserEntity) -> UserEntity:
        ...
