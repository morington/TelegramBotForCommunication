from typing import Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from src.core.domain.entities import FreelancerProfileEntity
from src.core.domain.interfaces.database.profile import AbstractFreelancerProfileRepo
from src.infrastructure.repository.models import FreelancerProfileAccountModel
from src.infrastructure.repository.query_base import Query


class FreelancerProfileQuery(Query, AbstractFreelancerProfileRepo):
    async def get_profile_by_user_id(self, user_id: int) -> Optional[FreelancerProfileEntity]:
        result = await self.session.execute(
            select(FreelancerProfileAccountModel)
            .where(FreelancerProfileAccountModel.user_id == user_id)
        )

        profile_model: Optional[FreelancerProfileAccountModel] = result.scalar_one_or_none()
        if not profile_model:
            return None

        return FreelancerProfileEntity.from_dict(profile_model.to_entity_dict())

    async def add_profile(self, profile: FreelancerProfileEntity) -> FreelancerProfileEntity:
        if not profile:
            raise ValueError("Entity must be mandatory")

        values = profile.to_dict_database()
        values.pop("languages")
        values.pop("stacks")

        result = await self.session.execute(
            insert(FreelancerProfileAccountModel)
            .values(values)
            .on_conflict_do_update(index_elements=["user_id"], set_={k: v for k, v in values.items() if k != "id"})
            .returning(FreelancerProfileAccountModel)
        )

        return FreelancerProfileEntity.from_dict(result.scalar_one_or_none().to_entity_dict())
