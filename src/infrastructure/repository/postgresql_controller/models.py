from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.decl_api import DeclarativeMeta

Base: DeclarativeMeta = declarative_base()


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return {
            "human_format": obj.strftime("%d.%m.%Y %H:%M:%S"),
            "iso": obj.isoformat(),
            "timestamp": obj.timestamp(),
            "datetime": obj,
        }
    return obj


class BaseModel:
    __table__ = None
    __tablename__ = None
    id: int

    def __str__(self) -> str:
        return self.__tablename__

    def __repr__(self) -> str:
        return f"{self.__tablename__} ID: {self.id}"

    @property
    def to_dict(self) -> dict:
        return {c.name: json_serial(getattr(self, c.name)) for c in self.__table__.columns}
