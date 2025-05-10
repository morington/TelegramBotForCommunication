from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.callbacks.user import SetRoleCallback, Commands
from src.core.domain.entities import UserEntity, FreelancerProfileEntity
from src.infrastructure.keyboard import generate_keyboard, template
from src.infrastructure.repository.models import RoleEnum
from src.use_cases.services.profile import FreelancerProfileService

router = Router(name=__name__)


@router.message(Command("start"))
async def start_command(
        message: Message,
        user_entity: UserEntity,
        freelancer_profile_query: FreelancerProfileService
) -> None:
    profile: FreelancerProfileEntity = await freelancer_profile_query.get_profile_by_user_id(user_id=user_entity.id)

    if not profile:
        text = (
            f"<b>Добро пожаловать, {user_entity.full_name}!</b>\n\n"
            f"Здесь ты сможешь:\n"
            f"  - Находить и публиковать заказы\n"
            f"  - Работать напрямую или через гаранта\n"
            f"  - Получать опыт и участвовать в активностях команды\n\n"
            f"<b>Для начала укажи, кто ты:</b>"
        )
        keyboard = generate_keyboard(
            buttons=[
                [
                    template("Я фрилансер", callback_data=SetRoleCallback(role=RoleEnum.freelancer)),
                    template("Я заказчик", callback_data=SetRoleCallback(role=RoleEnum.customer))
                ]
            ],
            inline=True
        )
    else:
        text = f"<b>С возвращением, {user_entity.full_name}!</b>"
        keyboard = generate_keyboard(
            buttons=[
                [
                    template("Личный кабинет", callback_data=Commands(command="profile_account"))
                ]
            ],
            inline=True
        )

    await message.answer(
        text=text,
        reply_markup=keyboard
    )
