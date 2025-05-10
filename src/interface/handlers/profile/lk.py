from typing import Optional

from aiogram import Router, F
from aiogram.types import CallbackQuery

from src.callbacks.user import SetRoleCallback, Commands
from src.core.domain.entities import FreelancerProfileEntity, UserEntity, DetectGitEntity
from src.infrastructure.repository.models import RoleEnum
from src.use_cases.profile import detect_git_platform, detect_url
from src.use_cases.services.profile import FreelancerProfileService

router = Router(name=__name__)


@router.callback_query(SetRoleCallback.filter())
async def creating_personal_account(
        callback_query: CallbackQuery,
        callback_data: SetRoleCallback,
        user_entity: UserEntity,
        freelancer_profile_query: FreelancerProfileService
) -> None:
    if callback_data.role == RoleEnum.freelancer:
        freelancer_entity = FreelancerProfileEntity(user_id=user_entity.id)
        profile: FreelancerProfileEntity = await freelancer_profile_query.add_profile(profile=freelancer_entity)

        detect_git: Optional[DetectGitEntity] = detect_git_platform(url=profile.git)
        git = f" ● {detect_git.value}: {profile.git}\n" if detect_git else ""

        site = f" ● Личный сайт: {profile.personal_site_url}\n" if detect_url(url=profile.personal_site_url) else ""

        build_languages = [
            f"<a href={lang.url}>{lang.name}</a>"
            for lang in profile.languages
        ]
        languages = f" ● Опыт в языках: {','.join(build_languages)}\n" if build_languages else ""

        build_stacks = [
            f"<a href={stack.url}>{stack.name}</a>"
            for stack in profile.stacks
        ]
        stacks = f" ● Стек: {','.join(build_stacks)}\n" if build_stacks else ""

        reviews = f"Найдено {profile.reviews_count} отзывов <a href='www.google.com'>[Посмотреть]</a>" if profile.reviews_count else "Отзывов пока нет"
        verification = "✅ Пользователь верифицирован" if profile.is_verified else "Пользователь не верифицирован"

        text = (
            f"<u>📂 Профиль: {user_entity.full_name}</u>\n"
            f"<i>{profile.bio or 'Био отсутствует'}</i>\n\n"
            f"<b>{git}</b>"
            f"<b>{site}</b>"
            f"<b>{languages}</b>"
            f"<b>{stacks}</b>"
            f"<b>{reviews}</b>\n"
            f"\n"
            f"<b>Карма: {profile.karma} <a href='www.google.com'>[Что это?]</a></b>\n"
            f"<i>{verification}</i> <b><a href='www.google.com'>[Что это?]</a></b>"
        )

        await callback_query.message.edit_text("<b>Отлично!</b> Личный кабинет успешно создан.\n<b>Вот твой профиль:</b>")
        await callback_query.message.answer(text=text)
    elif callback_data.role == RoleEnum.customer:
        await callback_query.answer(text="⚠️ Данная роль пока не реализована")
    else:
        await callback_query.answer(text="⚠️ Неизвестный тип роли")

    await callback_query.answer()


@router.callback_query(Commands.filter(F.command.in_({"profile_account",})))
async def profile_account(
        callback_query: CallbackQuery
) -> None:
    ...