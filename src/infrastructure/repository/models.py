import enum
from typing import Optional

from sqlalchemy import BigInteger, Integer, Text, Enum, DateTime, func, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.decl_api import DeclarativeMeta

Base: DeclarativeMeta = declarative_base()


class SQLAlchemyMixin :
    __table__ = None
    __tablename__ = None
    id: int

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
    freelancer = "freelancer"
    customer = "customer"


class OrderStatusEnum(str, enum.Enum):
    draft = "draft"
    moderation = "moderation"
    published = "published"
    taken = "taken"
    completed = "completed"
    rejected = "rejected"
    cancelled = "cancelled"


class UserModel(Base, SQLAlchemyMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str] = mapped_column(Text, nullable=True)
    first_name: Mapped[str] = mapped_column(Text, nullable=True)
    last_name: Mapped[str] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=True)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    orders = relationship("OrderModel", back_populates="creator")
    applications = relationship("ApplicationModel", back_populates="applicant")


class FreelancerProfileModel(Base, SQLAlchemyMixin):
    __tablename__ = "freelancer_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    github_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gitlab_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    personal_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_orders: Mapped[int] = mapped_column(Integer, default=0)

    user = relationship("UserModel", backref="freelancer_profile")


class CustomerProfileModel(Base, SQLAlchemyMixin):
    __tablename__ = "customer_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    total_orders: Mapped[int] = mapped_column(Integer, default=0)
    accepted_responses_ratio: Mapped[int] = mapped_column(Integer, nullable=True)

    user = relationship("UserModel", backref="customer_profile")


class OrderModel(Base, SQLAlchemyMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(Text)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[OrderStatusEnum] = mapped_column(Enum(OrderStatusEnum), default=OrderStatusEnum.draft)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default="now()")
    published_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_reason: Mapped[str] = mapped_column(Text, nullable=True)
    taken_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)

    creator = relationship("UserModel", foreign_keys=[created_by_user_id], back_populates="orders")
    applications = relationship("ApplicationModel", back_populates="order")


class ApplicationModel(Base, SQLAlchemyMixin):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default="now()")
    is_chosen: Mapped[bool] = mapped_column(Boolean, default=False)

    order = relationship("OrderModel", back_populates="applications")
    applicant = relationship("UserModel", back_populates="applications")
