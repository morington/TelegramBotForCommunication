import enum

from sqlalchemy import BigInteger, Integer, Text, Enum, DateTime, func, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.decl_api import DeclarativeMeta

Base: DeclarativeMeta = declarative_base()


class SQLAlchemyMixin :
    __table__ = None
    __tablename__ = None
    id: int
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __str__(self) -> str:
        return self.__tablename__

    def __repr__(self) -> str:
        return f"{self.__tablename__} ID: {self.id}"

    def to_dict(self) -> dict:
        """
        Serialized version (for logs, JSON output etc.).
        """
        return {
            c.name: self.json_serial(getattr(self, c.name))
            for c in self.__table__.columns
        }

    def to_entity_dict(self) -> dict:
        """
        Raw version for use in domain entities.
        """
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
        }



    @staticmethod
    def json_serial(obj):
        from datetime import datetime
        if isinstance(obj, datetime):
            return {
                "human_format": obj.strftime("%d.%m.%Y %H:%M:%S"),
                "iso": obj.isoformat(),
                "timestamp": obj.timestamp(),
                "datetime": obj,
            }
        return obj


class RoleEnum(str, enum.Enum):
    unknown = "unknown"
    freelancer = "freelancer"
    customer = "customer"


class UserModel(Base, SQLAlchemyMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str] = mapped_column(Text, nullable=True)
    first_name: Mapped[str] = mapped_column(Text, nullable=True)
    last_name: Mapped[str] = mapped_column(Text, nullable=True)
    full_name: Mapped[str] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=True)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), nullable=False)


class FreelancerProfileAccountModel(Base, SQLAlchemyMixin):
    __tablename__ = "freelancer_profile_account"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    bio: Mapped[str] = mapped_column(Text, nullable=True)
    git: Mapped[str] = mapped_column(Text, nullable=True)
    personal_site_url: Mapped[str] = mapped_column(Text, nullable=True)

    reviews_count: Mapped[int] = mapped_column(Integer, default=0)
    karma: Mapped[int] = mapped_column(Integer, default=0)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("UserModel", backref="profile", uselist=False)
    languages = relationship("ProfileAccountLanguageModel", back_populates="profile", cascade="all, delete-orphan")
    stacks = relationship("ProfileAccountStackModel", back_populates="profile", cascade="all, delete-orphan")


class ProfileAccountLanguageModel(Base, SQLAlchemyMixin):
    __tablename__ = "profile_account_language"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    profile_id: Mapped[int] = mapped_column(ForeignKey("freelancer_profile_account.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=True)

    profile = relationship("FreelancerProfileAccountModel", back_populates="languages")


class ProfileAccountStackModel(Base, SQLAlchemyMixin):
    __tablename__ = "profile_account_stack"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    profile_id: Mapped[int] = mapped_column(ForeignKey("freelancer_profile_account.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=True)

    profile = relationship("FreelancerProfileAccountModel", back_populates="stacks")
