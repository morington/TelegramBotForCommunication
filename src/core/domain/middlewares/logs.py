import uuid
from typing import Any, Awaitable, Callable

import structlog
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from src import Loggers

logger: structlog.BoundLogger = structlog.getLogger(Loggers.main.name)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        with structlog.contextvars.bound_contextvars(_trace=uuid.uuid4().hex):
            log_params = {
                "user_id": getattr(event.event.from_user, 'id', None),
                "chat_id": getattr(event.event.chat, 'id', None) if isinstance(event.event, Message) else getattr(event.event.message.chat, 'id', None)
            }

            if isinstance(event.event, Message):
                message_type, specific_params = self._extract_message_params(event.event)
                log_params.update(specific_params)
                await logger.adebug(message_type, **log_params)

            elif isinstance(event.event, CallbackQuery):
                await logger.adebug(
                    "Request `CallbackQuery`",
                    _data=event.event.data,
                    user_id=event.event.from_user.id,
                    chat_id=event.event.message.chat.id
                )
            else:
                await logger.adebug("Unknown Request", _data=event.to_dict())

            result = await handler(event, data)
            if getattr(result, "name", None) == "UNHANDLED":
                await logger.awarning("Unhandled Request")
            return result

    @staticmethod
    def _extract_message_params(event: Message) -> tuple:
        """Helper function to extract message type and specific logging parameters."""
        if text := event.text:
            return "Request `Message`", {"_message": text}
        if audio := event.audio:
            return "Request `Audio`", {"file_id": audio.file_id, "file_unique_id": audio.file_unique_id}
        if sticker := event.sticker:
            return "Request `Sticker`", {"file_id": sticker.file_id, "file_unique_id": sticker.file_unique_id}
        if animation := event.animation:
            return "Request `Animation`", {"file_id": animation.file_id, "file_unique_id": animation.file_unique_id}
        if photo := event.photo:
            return "Request `Photo`", {"file_id": photo[-1].file_id, "file_unique_id": photo[-1].file_id}
        if poll := event.poll:
            return "Request `Poll`", {
                "poll_id": poll.id,
                "question": poll.question,
                "options": [option.text for option in poll.options]
            }
        if video := event.video:
            return "Request `Video`", {"file_id": video.file_id, "file_unique_id": video.file_unique_id}
        if document := event.document:
            return "Request `Document`", {
                "file_name": document.file_name,
                "file_id": document.file_id,
                "file_unique_id": document.file_unique_id
            }

        return "Unknown Request", event.to_dict()
