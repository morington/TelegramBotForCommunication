import structlog


class BaseError(Exception):
    """ Basic class of errors """

    message: str = "BaseError"

    def __init__(self, logger: structlog.BoundLogger, error: bool = True, **kwargs):
        if error:
            logger.error(self.message, **kwargs, exc_info=True)
        else:
            logger.info(self.message, **kwargs)

        super().__init__(self.message)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__doc__ = cls.message


class UnexpectedErrorInBotStartup(BaseError):
    message = "An unforeseen error was occurred when starting the bot"


class UnexpectedErrorInBotOperation(BaseError):
    message = "An unforeseen error in the work of the bot occurred"
