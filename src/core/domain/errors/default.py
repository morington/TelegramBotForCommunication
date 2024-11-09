import structlog


class BaseError(Exception):
    """Базовый класс ошибок"""

    message: str = "BaseError"

    def __init__(self, logger: structlog.BoundLogger, error: bool = True, **kwargs):
        if error:
            logger.error(self.message, **kwargs, exc_info=True)
        else:
            logger.info(self.message, **kwargs)

        super().__init__(self.message)


class UnexpectedErrorInBotStartup(BaseError):
    """Неизвестная ошибка при запуске бота"""

    message = "Произошла непредвиденная ошибка при запуске бота"


class UnexpectedErrorInBotOperation(BaseError):
    """Неизвестная ошибка в работе бота"""

    message = "Произошла непредвиденная ошибка в работе бота"
