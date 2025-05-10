from typing import Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from src.core.domain.entities import UserEntity
from src.core.domain.interfaces.database.user import AbstractUserRepo
from src.infrastructure.repository.models import UserModel
from src.infrastructure.repository.query_base import Query


class UserQuery(Query, AbstractUserRepo):
    async def get_user_by_telegram_id(self, user_telegram_id: int) -> Optional[UserEntity]:
        result = await self.session.execute(
            select(UserModel)
            .where(UserModel.telegram_id == user_telegram_id)
        )

        user_model: Optional[UserModel] = result.scalar_one_or_none()
        if not user_model:
            return None

        return UserEntity.from_dict(user_model.to_entity_dict())


    async def add_user(self, user: UserEntity) -> UserEntity:
        if not user:
            raise ValueError("Entity must be mandatory")

        values = user.to_dict_database()

        result = await self.session.execute(
            insert(UserModel)
            .values(values)
            .on_conflict_do_update(index_elements=["telegram_id"], set_={k: v for k, v in values.items() if k != "id"})
            .returning(UserModel)
        )

        return UserEntity.from_dict(result.scalar_one_or_none().to_entity_dict())
