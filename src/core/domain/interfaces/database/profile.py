from abc import ABC, abstractmethod
from typing import Optional

from src.core.domain.entities import FreelancerProfileEntity


class AbstractFreelancerProfileRepo(ABC):
    @abstractmethod
    async def get_profile_by_user_id(self, user_id: int) -> Optional[FreelancerProfileEntity]:
        raise NotImplementedError

    @abstractmethod
    async def add_profile(self, profile: FreelancerProfileEntity) -> FreelancerProfileEntity:
        raise NotImplementedError
