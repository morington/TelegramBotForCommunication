import structlog
from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src import Settings, Loggers
from src.core.domain.middlewares.database import SessionMiddleware
from src.core.domain.middlewares.ensure_user import EnsureUserMiddleware
from src.core.domain.middlewares.errors import ErrorMiddleware
from src.core.domain.middlewares.logs import LoggingMiddleware
from src.core.domain.middlewares.nats_client import NatsClientMiddleware
from src.infrastructure.configuration.dynaconf_controller.main import Config
from src.infrastructure.natslib.client import NatsClient
from src.interface.api.ping import router_ping
from src.interface.handlers import default

logger: structlog.BoundLogger = structlog.getLogger(Loggers.main.name)


class WebhookConstructor:
    def __init__(self, domain: str):
        self.url = domain
        self.webhook_path = "/bot_aiogram"

    @property
    def webhook(self) -> str:
        return f"{self.url}{self.webhook_path}"


class TelegramBotManager:
    def __init__(self) -> None:
        # Загрузка конфигурации
        config_loader = Config(env="DEV", url_templates={
            "postgresql": "postgresql+asyncpg",
            "redis": "redis",
            "nats": "nats"
        })
        try:
            self.settings = Settings(**config_loader.raw)
        except ValidationError as e:
            print("Ошибка конфигурации:\n")
            for error in e.errors():
                loc = ".".join(str(x) for x in error['loc'])
                msg = error['msg']
                print(f"  - {loc}: {msg}")
            raise SystemExit(1)

        self.nats_client = NatsClient(servers=self.settings.nats_url)

        # Создание webhook
        self.webhook_build = WebhookConstructor(domain=self.settings.application.domain)

        # Инициализация RedisStorage
        redis_storage = RedisStorage.from_url(
            url=self.settings.redis_url,
            key_builder=DefaultKeyBuilder(with_destiny=True, with_bot_id=True),
        )

        # Инициализация бота
        self.session = AiohttpSession()
        self.app = web.Application()
        self.bot = Bot(
            token=self.settings.application.token,
            session=self.session,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True)
        )

        # Инициализация диспетчера
        self.dp = Dispatcher(storage=redis_storage)
        self.dp.startup.register(self.on_startup)

        # Обработчик экземпляра бота
        SimpleRequestHandler(dispatcher=self.dp, bot=self.bot).register(self.app, path=self.webhook_build.webhook_path)

        # Установка
        setup_application(self.app, self.dp, bot=self.bot)

        # Добавление кастомных роутеров
        self.app.router.add_get("/ping", router_ping)

    async def on_startup(self, dispatcher: Dispatcher, bot: Bot) -> None:
        """Действия перед запуском"""
        # Подключение к NATS JetStream
        await self.nats_client.connect()

        # await bot.set_my_commands([BotCommand(command='help', description='Помощь')])

        _url = self.webhook_build.webhook

        # Инициализация middlewares
        await self.middlewares_installer(dispatcher)

        # Инициализация роутеров
        route = Router(name="main")

        route.include_router(default.router)

        dispatcher.include_router(route)
        await logger.adebug("Router installed")

    async def middlewares_installer(self, dispatcher: Dispatcher) -> None:
        """Инициализация middlewares"""
        dispatcher.update.middleware(ErrorMiddleware())
        dispatcher.update.middleware(LoggingMiddleware())

        engine: AsyncEngine = create_async_engine(url=self.settings.postgresql_url, echo=False)
        dispatcher.update.middleware(SessionMiddleware(engine=engine))

        dispatcher.update.middleware(NatsClientMiddleware(nats_client=self.nats_client))

        dispatcher.update.middleware(EnsureUserMiddleware())

    def start(self) -> None:
        """Запуск приложения"""
        _d = {"host": self.settings.application.host, "port": self.settings.application.port}
        logger.info("Run app", **_d)
        web.run_app(self.app, **_d)

    async def start_polling(self) -> None:
        await self.bot.delete_webhook()
        await logger.ainfo("Start polling")
        await self.dp.start_polling(self.bot)

    async def stop(self) -> None:
        """Остановка приложения"""
        await logger.adebug("Stop app")
        await self.app.shutdown()
        await self.session.close()
