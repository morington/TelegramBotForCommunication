from pydantic import BaseModel
from typing import Optional, List, Any

class PostgresqlModel(BaseModel):
    host: Optional[str] = None
    port: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    path: Optional[str] = None


class RedisModel(BaseModel):
    host: Optional[str] = None
    port: Optional[str] = None


class ApplicationModel(BaseModel):
    host: Optional[str] = None
    domain: Optional[str] = None
    port: Optional[int] = None
    token: Optional[str] = None
    administrators: Optional[List[int]] = None
    chief_administrator: Optional[int] = None


class NatsOtherPortsModel(BaseModel):
    monitoring: Optional[str] = None


class NatsModel(BaseModel):
    host: Optional[str] = None
    port: Optional[str] = None
    other_ports: Optional[NatsOtherPortsModel] = None


class Settings(BaseModel):
    postgresql: Optional[PostgresqlModel] = None
    redis: Optional[RedisModel] = None
    application: Optional[ApplicationModel] = None
    nats: Optional[NatsModel] = None
    postgresql_url: Optional[str] = None
    redis_url: Optional[str] = None
    nats_url: Optional[str] = None


