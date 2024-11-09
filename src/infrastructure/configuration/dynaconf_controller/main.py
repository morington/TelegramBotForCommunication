from pathlib import Path
from typing import Any, Literal

import yarl
from dynaconf import Dynaconf


class ConfigurationParserFromDynaconf:
    """
    Класс для загрузки и обработки конфигурационных файлов, а также создания URL для сервисов.

    Поддерживает загрузку конфигураций в зависимости от окружения (dev, release) и
    динамическое создание URL для сервисов (Redis, PostgreSQL).

    `self.data` хранит в себе данные
    """

    def __init__(
        self,
        *settings_files: Path,
        environment: Literal["DEV", "RELEASE"] = "DEV",
        base_dir: Path = None,
    ):
        """
        Инициализация парсера конфигураций.

        :param settings_files: Пути к конфигурационным файлам (например, settings.yml, .secrets.yml).
        :param environment: Опционально: режим окружения (dev или release). Если не указан, будет
                            использована переменная окружения ENV.
        :param base_dir: Корневая директория для поиска файлов конфигурации. Если не указана,
                         используется текущий рабочий каталог.
        """
        self.base_dir = (
            base_dir or Path.cwd()
        )  # Корневой каталог для конфигураций (по умолчанию cwd)
        self.settings_files = [
            self.base_dir / f for f in settings_files
        ]  # Абсолютные пути к файлам
        self.environment: Literal["DEV", "RELEASE"] = (
            environment  # Приоритет переменной окружения
        )
        self.data: dict[str, Any] = {}

        self._validate_settings_files()
        self._load_configuration()
        self.create_service_urls()

    def _validate_settings_files(self) -> None:
        """
        Проверяет существование всех указанных конфигурационных файлов.
        Выбрасывает исключение, если один из файлов не найден.
        """
        for file in self.settings_files:
            if not file.exists():
                raise FileNotFoundError(f"Файл конфигурации не найден: {file}")

    def _load_configuration(self) -> None:
        """
        Загружает конфигурации из указанных файлов с помощью dynaconf.
        """
        self.config_box = Dynaconf(settings_files=[*self.settings_files])
        self.data = self.config_box.get(self.environment)

        # Загружаем данные в виде словаря
        # self.data = self.config.as_dict()

    def create_service_urls(self) -> None:
        """
        Динамическое создание URL для сервисов (Redis, PostgreSQL).
        """
        redis_data = self.data.get("REDIS", {})
        postgresql_data = self.data.get("POSTGRESQL", {})
        nats_data = self.data.get("NATS", {})

        if redis_data:
            self.data["redis_url"] = yarl.URL.build(
                scheme="redis",
                host=redis_data.get("host"),
                port=redis_data.get("port"),
                path=f"/{redis_data.get('path', '')}",
            ).human_repr()

        if postgresql_data:
            self.data["database_url"] = yarl.URL.build(
                scheme="postgresql+asyncpg",
                user=postgresql_data.get("user"),
                password=postgresql_data.get("password"),
                host=postgresql_data.get("host"),
                port=postgresql_data.get("port"),
                path=f"/{postgresql_data.get('path', '')}",
            ).human_repr()

        if nats_data:
            self.data["nats_url"] = yarl.URL.build(
                scheme="nats", host=nats_data.get("host"), port=nats_data.get("port")
            ).human_repr()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получает значение из загруженной конфигурации, поддерживая точечную нотацию для вложенных данных.

        :param key: Ключ конфигурации (например, 'redis.port' для получения порта Redis).
        :param default: Значение по умолчанию, если ключ не найден.
        :return: Значение конфигурации или default.
        """
        keys = key.split(".")
        value = self.data

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default


if __name__ == "__main__":
    # Задаем файлы конфигурации относительно корня проекта
    files = [Path("config/settings.yml"), Path("config/.secrets.yml")]

    # Инициализация парсера конфигурации с указанием корневой директории
    config_parser = ConfigurationParserFromDynaconf(
        *files, base_dir=Path("D:/Devs/Parser/parser_master")
    )

    # Получение значения, например, порта Redis
    redis_port = config_parser.get("REDIS.port", default=1)
    print(redis_port)  # 6379 | default = 1

    # Получение URL сервисов
    redis_url = config_parser.get("redis_url")
    database_url = config_parser.get("database_url")

    print(f"Redis URL: {redis_url}")
    print(f"Database URL: {database_url}")
