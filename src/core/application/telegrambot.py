from functools import partial

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
from jinja2 import Template
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.core.domain.filters.access import AccessFilter
from src.core.domain.middlewares.database import SessionMiddleware
from src.core.domain.middlewares.errors import ErrorMiddleware
from src.core.domain.middlewares.logs import LoggingMiddleware
from src.core.domain.webhook import WebhookConstructor
from src.infrastructure.configuration.dynaconf_controller.main import ConfigurationParserFromDynaconf, load_configuration
from src.interface.api.ping import router_ping
from src.interface.api.errors.errors import router_errors
from src.interface.handlers import default, profile
from src.project import BASE_PATH, MODE

logger: structlog.BoundLogger = structlog.getLogger("TelegramBot")


class TelegramBotManager:
    def __init__(self) -> None:
        # Загрузка конфигураций
        self.configuration: ConfigurationParserFromDynaconf = load_configuration(base_dir=BASE_PATH, environment=MODE)
        self.telegram_config = self.configuration.get("telegram_bot")

        # Создание webhook
        self.webhook_build = WebhookConstructor(domain=self.telegram_config.domain)

        # Инициализация RedisStorage
        redis_storage = RedisStorage.from_url(
            url=self.configuration.get("redis_url"),
            key_builder=DefaultKeyBuilder(with_destiny=True, with_bot_id=True),
        )

        # Инициализация бота
        self.session = AiohttpSession()
        self.app = web.Application()
        self.bot = Bot(
            token=self.telegram_config.token,
            session=self.session,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True)
        )

        # Инициализация диспетчера
        self.main_dp = Dispatcher(storage=redis_storage)
        self.main_dp.startup.register(self.on_startup)

        # Обработчик экземпляра бота
        SimpleRequestHandler(dispatcher=self.main_dp, bot=self.bot).register(self.app, path=self.webhook_build.webhook_path)

        # Установка
        setup_application(self.app, self.main_dp, bot=self.bot)

        # Добавление кастомных роутеров
        self.app.router.add_get("/ping", router_ping)

        template_path = BASE_PATH / 'interface/api/errors/template.html'
        with template_path.open('r', encoding='utf-8') as file:
            template_string = file.read()

        template = Template(template_string)
        self.app.router.add_get("/errors", partial(router_errors, template=template, redis=redis_storage.redis))

    async def on_startup(self, dispatcher: Dispatcher, bot: Bot) -> None:
        """Действия перед запуском"""

        await bot.set_my_commands([
            BotCommand(command='help', description='Помощь'),
        ])

        _url = self.webhook_build.webhook

        if self.telegram_config.delete_update:
            await logger.adebug("Delete last updates")
            await bot.delete_webhook(drop_pending_updates=True)

        await bot.set_webhook(
            _url,
            allowed_updates=[
                "message",
                "callback_query",
                "chat_member",
                "my_chat_member",
            ],
        )
        await logger.adebug(f"Installed WebHook at: {_url[:-10] + '*' * 10}")

        # Инициализация middlewares
        await self.middlewares_installer(dispatcher)

        # Инициализация роутеров
        route = Router(name="main")
        access_filter = AccessFilter(moderators=self.telegram_config.moderators, admin=self.telegram_config.admin)
        route.message.filter(access_filter)
        route.callback_query.filter(access_filter)

        route.include_router(default.router)
        route.include_router(profile.router)

        dispatcher.include_router(route)
        await logger.adebug("Router installed")

    async def middlewares_installer(self, dispatcher: Dispatcher) -> None:
        """Инициализация middlewares"""
        # Подключение к базе данных
        dispatcher.update.outer_middleware(LoggingMiddleware())
        engine: AsyncEngine = create_async_engine(url=self.configuration.get("database_url"), echo=False)
        dispatcher.update.middleware(SessionMiddleware(engine=engine))
        # dispatcher.update.middleware(ErrorMiddleware(admin=self.telegram_config.admin, base_url=self.telegram_config.domain))

    def start(self) -> None:
        """Запуск приложения"""
        logger.debug("Run app", host=self.telegram_config.host, port=self.telegram_config.port)
        web.run_app(self.app, host=self.telegram_config.host, port=self.telegram_config.port)

    def stop(self) -> None:
        """Остановка приложения"""
        logger.debug("Stop app")
        self.app.shutdown()
        self.session.close()
