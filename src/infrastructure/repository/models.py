from sqlalchemy.ext.declarative import declarative_base
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
