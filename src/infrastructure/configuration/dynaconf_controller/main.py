from typing import Any, Dict, Optional, List, Union
from dynaconf import Dynaconf
import os

from yarl import URL


class AttrDict(dict):
    """
    Recursive dict with attribute access.
    """

    def __getattr__(self, item):
        val = self.get(item)
        if isinstance(val, dict):
            return AttrDict(val)
        return val

    def __setattr__(self, key, value):
        self[key] = value


class Config:
    """
    Конфигурационный загрузчик на базе Dynaconf.
    Возвращает данные для Pydantic-модели и создает URL-свойства по секциям.
    """

    def __init__(self, env: str = "DEV", url_templates: Optional[Dict[str, str]] = None) -> None:
        self._dynaconf = Dynaconf(
            settings_files=["src/config/settings.yml"],
            load_dotenv=True,
        )
        self._env = env.lower()
        self._url_templates = url_templates or {}

        self._data = self._load_config_tree()
        self._generate_url_properties()

    @property
    def raw(self) -> Dict[str, Any]:
        """
        Получить конфигурацию как dict.

        Documentation
        Returns:
            Dict[str, Any] - словарь с конфигурацией для передачи в Settings.
        """
        return dict(self._data)

    def build_url(self, section: str, scheme: str) -> Optional[URL]:
        """
        Собирает URL по данным из секции.

        Args:
            section [str] - имя секции (например, 'postgresql').
            scheme [str] - схема подключения (например, 'postgresql+asyncpg').

        Returns:
            Optional[URL] - собранный URL или None, если секция отсутствует.
        """
        cfg = self._data.get(section)
        if not cfg:
            return None

        host = getattr(cfg, "host", "localhost") or "localhost"
        port = int(cfg.port) if getattr(cfg, "port", None) else None
        user = getattr(cfg, "user", None)
        password = getattr(cfg, "password", None)

        db_env_key = f"{section.upper()}__DB"
        db_name = os.getenv(db_env_key, "").strip()
        path = f"/{db_name}" if db_name else ""

        return URL.build(
            scheme=scheme or "",
            user=user,
            password=password,
            host=host,
            port=port,
            path=path
        )

    def _generate_url_properties(self) -> None:
        """
        Генерирует URL-свойства и записывает их только в _data.
        """
        for section, scheme in self._url_templates.items():
            url = self.build_url(section, scheme)
            self._data[f"{section}_url"] = str(url) if url else None

    def _resolve_env_value(self, keys: List[str]) -> Optional[str]:
        env_key = "__".join(k.upper() for k in keys)
        return os.getenv(env_key)

    def _load_config_tree(self) -> AttrDict:
        def resolve_section(data: Union[Dict[str, Any], Any], prefix: List[str]) -> Any:
            if isinstance(data, dict):
                return AttrDict({
                    k: resolve_section(v, prefix + [k])
                    for k, v in data.items()
                })
            return data if data is not None else self._resolve_env_value(prefix)

        base = self._dynaconf.get(self._env, {}) or {}
        return AttrDict({
            section: resolve_section(data, [section])
            for section, data in base.items()
        })


if __name__ == "__main__":
    from src import Settings

    config_loader = Config(env="DEV", url_templates={
        "postgresql": "postgresql+asyncpg",
        "redis": "redis",
        "nats": "nats"
    })
    settings = Settings(**config_loader.raw)

    print(settings.postgresql.host)

    # Теперь доступ к URL-свойствам только через raw/settings
    print(settings.postgresql_url)
    print(settings.redis_url)
    print(settings.nats_url)
