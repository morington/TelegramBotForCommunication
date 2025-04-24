import dataclasses
from typing import Optional, Dict, List
import structlog
from enum import Enum
import logging.config
import os
import sys
from structlog.typing import EventDict


class LoggerError(Exception):
    """Base exception class for logger-related errors."""


class LoggerNotFoundError(LoggerError):
    """Raised when a requested logger is not found."""


def add_caller_details(_: logging.Logger, __: str, event_dict: EventDict) -> EventDict:
    """Add caller details (filename, function, line number) to the event dictionary.

    Args:
        _: Logger instance (unused).
        __: Method name (unused).
        event_dict: The event dictionary to augment.

    Returns:
        EventDict: Updated event dictionary with caller details.
    """
    filename = event_dict.pop("filename")
    func_name = event_dict.pop("func_name")
    lineno = event_dict.pop("lineno")
    event_dict["logger"] = f"{filename}:{func_name}:{lineno}"
    return event_dict


@dataclasses.dataclass(slots=True)
class LoggerReg:
    """Configuration for a logger instance."""

    class Level(Enum):
        DEBUG = "DEBUG"
        INFO = "INFO"
        WARNING = "WARNING"
        ERROR = "ERROR"
        CRITICAL = "CRITICAL"
        NONE = None

    name: str
    level: Level = Level.DEBUG
    propagate: bool = False


class SetupLogger:
    """Configures logging with structlog for console output."""

    CONSOLE_HANDLER = "console"
    CONSOLE_FORMATTER = "console_formatter"
    JSONFORMAT_HANDLER = "jsonformat"
    JSONFORMAT_FORMATTER = "jsonformat_formatter"

    def __init__(self, name_registration: Optional[List[LoggerReg]], developer_mode: bool = False) -> None:
        """Initialize logger setup with given registrations.

        Args:
            name_registration: List of logger configurations. If None, a default logger is used.
            developer_mode: If True, use human-readable console output; otherwise, use JSON.
        """
        self.name_registration = name_registration or [LoggerReg(name="", level=LoggerReg.Level.DEBUG)]
        self.name_registration.append(LoggerReg(name="confhub", level=LoggerReg.Level.INFO))
        self.developer_mode = developer_mode
        self.module_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        self.init_structlog()

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} dev:{sys.stderr.isatty()}; Registered {len(self.name_registration)} loggers>"

    @property
    def renderer(self) -> str:
        """Determine the renderer based on environment or developer mode.

        Returns:
            str: Handler name for console or JSON output.
        """
        if sys.stderr.isatty() or os.environ.get("MODE_DEV", self.developer_mode):
            return self.CONSOLE_HANDLER
        return self.JSONFORMAT_HANDLER

    @property
    def timestamper(self) -> structlog.processors.TimeStamper:
        """Provide a timestamp processor.

        Returns:
            TimeStamper: Processor for adding timestamps to logs.
        """
        return structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")

    def preprocessors(self, extended: bool = False) -> List[any]:
        """Define structlog preprocessors for log processing.

        Args:
            extended: If True, include additional preprocessors for advanced logging.

        Returns:
            List[any]: List of configured preprocessors.
        """
        base_preprocessors = [
            self.timestamper,
            structlog.stdlib.add_log_level,
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.CallsiteParameterAdder(
                {
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                }
            ),
            add_caller_details,
        ]
        if extended:
            return (
                [
                    structlog.contextvars.merge_contextvars,
                    structlog.stdlib.filter_by_level,
                ]
                + base_preprocessors
                + [
                    structlog.stdlib.PositionalArgumentsFormatter(),
                    structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
                ]
            )
        return base_preprocessors

    def init_structlog(self) -> None:
        """Initialize structlog with logging configuration."""
        handlers = {
            self.CONSOLE_HANDLER: {
                "class": "logging.StreamHandler",
                "formatter": self.CONSOLE_FORMATTER,
            },
            self.JSONFORMAT_HANDLER: {
                "class": "logging.StreamHandler",
                "formatter": self.JSONFORMAT_FORMATTER,
            },
        }

        logging.config.dictConfig({
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                self.JSONFORMAT_FORMATTER: {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.processors.JSONRenderer(),
                    "foreign_pre_chain": self.preprocessors(),
                },
                self.CONSOLE_FORMATTER: {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.dev.ConsoleRenderer(),
                    "foreign_pre_chain": self.preprocessors(),
                },
            },
            "handlers": handlers,
            "loggers": {
                logger_setting.name: {
                    "handlers": [self.renderer],
                    "level": logger_setting.level.value,
                    "propagate": logger_setting.propagate,
                }
                for logger_setting in self.name_registration
            },
        })

        structlog.configure(
            processors=self.preprocessors(extended=True),
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )


class InitLoggers:
    """Base class for project-specific logger configurations.

    Inherit from this class and define loggers as class attributes.
    """

    def __init__(self, developer_mode: bool = False) -> None:
        """Initialize logger instances from class attributes.

        Args:
            developer_mode: Enable human-readable output if True.

        Raises:
            LoggerError: If no loggers are defined in the subclass.
        """
        self._loggers: Dict[str, LoggerReg] = {
            name: getattr(self, name)
            for name in dir(self)
            if isinstance(getattr(self, name), LoggerReg)
        }
        if not self._loggers:
            raise LoggerError("No loggers defined in the subclass")
        self.setup = SetupLogger(
            name_registration=list(self._loggers.values()),
            developer_mode=developer_mode,
        )
        self._logger_instances: Dict[str, structlog.BoundLogger] = {
            reg.name: structlog.getLogger(reg.name)
            for reg in self._loggers.values()
        }

    def __getattr__(self, name: str) -> structlog.BoundLogger:
        """Access logger instances as attributes.

        Args:
            name: Name of the logger to retrieve.

        Returns:
            BoundLogger: Configured logger instance.

        Raises:
            LoggerNotFoundError: If the logger name is not registered.
        """
        try:
            return self._logger_instances[name]
        except KeyError:
            raise LoggerNotFoundError(f"Logger '{name}' not found. Available loggers: {list(self._logger_instances.keys())}")