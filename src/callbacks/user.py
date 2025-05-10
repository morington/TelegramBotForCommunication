from aiogram.filters.callback_data import CallbackData

from src.infrastructure.repository.models import RoleEnum


class SetRoleCallback(CallbackData, prefix="setrole"):
    role: RoleEnum


class Commands(CallbackData, prefix="commands"):
    command: str
