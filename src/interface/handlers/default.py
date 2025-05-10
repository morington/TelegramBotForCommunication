from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.core.domain.entities import UserEntity

router = Router(name=__name__)


@router.message(Command("start"))
async def start_command(message: Message, user_entity: UserEntity) -> None:
    await message.answer(
        f"<b>Приветствую {user_entity.full_name}!</b>\n"
        f"Добро пожаловать в тестовую версию бота!"
    )
