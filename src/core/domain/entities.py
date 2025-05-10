from dataclasses import dataclass, asdict, fields, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Union, Optional, List

from src.infrastructure.repository.models import RoleEnum


@dataclass
class DataClassMixin:
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        raw = asdict(self)
        for f in fields(self):
            value = raw[f.name]
            if isinstance(value, Enum):
                raw[f.name] = value.name
        return raw

    def to_dict_database(self) -> Dict[str, Any]:
        data = self.to_dict()
        data.pop("id")
        data.pop("created_at")
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "DataClassMixin":
        # only keep known fields
        allowed_fields = {f.name: f.type for f in fields(cls)}
        clean_data = {}

        for key, value in data.items():
            if key not in allowed_fields:
                continue

            field_type = allowed_fields[key]

            # Handle Optional[...] by unwrapping
            origin_type = getattr(field_type, "__origin__", None)
            if origin_type is Union:
                args = field_type.__args__
                enum_type = next((arg for arg in args if isinstance(arg, type) and issubclass(arg, Enum)), None)
            elif isinstance(field_type, type) and issubclass(field_type, Enum):
                enum_type = field_type
            else:
                enum_type = None

            # Convert str to Enum
            if enum_type and isinstance(value, str):
                try:
                    value = enum_type[value]
                except KeyError:
                    pass  # fallback: keep string

            clean_data[key] = value

        return cls(**clean_data)


@dataclass
class UserEntity(DataClassMixin):
    id: Optional[int] = None
    telegram_id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: str = "..."
    url: Optional[str] = None
    role: RoleEnum = RoleEnum.unknown


@dataclass
class ProfileLanguageEntity(DataClassMixin):
    id: Optional[int] = None
    profile_id: int = 0
    name: str = ""
    url: Optional[str] = None


@dataclass
class ProfileStackEntity(DataClassMixin):
    id: Optional[int] = None
    profile_id: int = 0
    name: str = ""
    url: Optional[str] = None


@dataclass
class FreelancerProfileEntity(DataClassMixin):
    id: Optional[int] = None
    user_id: Optional[int] = None
    bio: Optional[str] = None
    git: Optional[str] = None
    personal_site_url: Optional[str] = None
    reviews_count: int = 0
    karma: int = 0
    is_verified: bool = False
    languages: List[ProfileLanguageEntity] = field(default_factory=list)
    stacks: List[ProfileStackEntity] = field(default_factory=list)


class DetectGitEntity(Enum):
    gitlab = "Gitlab"
    github = "Github"