from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name=__name__)


@router.message(Command("start"))
async def start_command(message: Message) -> None:
    await message.answer("Добро пожаловать!")
