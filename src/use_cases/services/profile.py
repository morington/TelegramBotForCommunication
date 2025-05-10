from typing import Optional

from src.core.domain.entities import FreelancerProfileEntity
from src.core.domain.interfaces.database.profile import AbstractFreelancerProfileRepo


class FreelancerProfileService:
    def __init__(self, repo: AbstractFreelancerProfileRepo) -> None:
        self.repo = repo

    async def get_profile_by_user_id(self, user_id: int) -> Optional[FreelancerProfileEntity]:
        return await self.repo.get_profile_by_user_id(user_id=user_id)

    async def add_profile(self, profile: FreelancerProfileEntity) -> FreelancerProfileEntity:
        return await self.repo.add_profile(profile=profile)
