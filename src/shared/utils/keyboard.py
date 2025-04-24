from typing import Optional, Union, List, Callable, Any, Awaitable, Type
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton, Message, CallbackQuery,
)
from aiogram.filters.callback_data import CallbackData


def template(
    text: str,
    callback_data: Optional[Union[str, CallbackData]] = None,
    **kwargs
) -> dict:
    """
    Шаблон для кнопок.

    ##################################
    Пример использования:
    ##################################

    template(
        text="⬅️ Назад", callback_data=self.callback_factory(page=self.page - 1).pack()
    )
    template(
        text="Group 1", callback_data="group_1"
    )

    :param text: Текст кнопки.
    :param callback_data: Строка или объект CallbackData для inline-кнопок.
    :param kwargs: Дополнительные параметры кнопки (например, url, switch_inline_query).
    :return: Словарь с параметрами кнопки.
    """
    if isinstance(callback_data, CallbackData):
        callback_data = callback_data.pack()

    return {"text": text, "callback_data": callback_data, **kwargs}


def generate_keyboard(
    buttons: List[Union[str, list, dict]],
    inline: bool = True,
    resize_keyboard: bool = True,
    is_persistent: bool = False,
) -> Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]:
    """
    Генератор клавиатур.

    ##################################
    Пример использования:
    ##################################

    buttons = [
        self.item_renderer(item)
        for item in self.items
    ] + [
        [
            template(
                text="⬅️ Назад", callback_data=self.callback_factory(page=self.page - 1).pack()
            ) if self.page > 0 else None,
            template(
                text="Вперед ➡️", callback_data=self.callback_factory(page=self.page + 1).pack()
            ) if self.page < total_pages - 1 else None,
        ]
    ]

    keyboard = generate_keyboard(buttons, inline=inline)

    :param buttons: Список кнопок. Может быть списком строк, списком списков, или словарей.
    :param inline: True для InlineKeyboardMarkup, False для ReplyKeyboardMarkup.
    :param resize_keyboard: Уменьшать ли клавиатуру (только для ReplyKeyboardMarkup).
    :param is_persistent: Постоянная клавиатура (только для ReplyKeyboardMarkup).
    :return: Объект клавиатуры (Inline или Reply).
    """
    keyboard: list = []

    if inline:
        for button in buttons:
            if button:
                if isinstance(button, list):
                    keyboard.append([InlineKeyboardButton(**btn) for btn in button if btn])
                elif isinstance(button, dict):
                    keyboard.append([InlineKeyboardButton(**button)])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    else:
        for item in buttons:
            if item:
                if isinstance(item, list):
                    keyboard.append([KeyboardButton(text=text) for text in item if text])
                elif isinstance(item, str):
                    keyboard.append([KeyboardButton(text=item)])

        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=resize_keyboard, is_persistent=is_persistent)


class Paginator:
    """
    ##################################
    Пример использования Paginator
    ##################################

    GROUP_PER_PAGE = 5


    class GroupPaginationCallbackFactory(CallbackData, prefix="group_pagination"):
        page: int = 0


    class ToggleGroupCallbackFactory(CallbackData, prefix="group_action"):
        group_id: int


    @router.message(Command("show_groups"))
    async def show_groups_command(message: Message, group_query: GroupQuery):
        page = 0

        paginator = Paginator(
            message,
            items=await group_query.get_groups_paginated(limit=GROUP_PER_PAGE, offset=page * GROUP_PER_PAGE),
            total_count=await group_query.get_total_groups_count(),
            item_renderer=lambda group: template(
                text=f"{group['id']}:{group['name']} {group['chat_id']}",
                callback_data=ToggleGroupCallbackFactory(group_id=group['chat_id'])
            ),
            paginate_callback_factory=GroupPaginationCallbackFactory,
            items_per_page=GROUP_PER_PAGE,
            page=page
        )

        # Отправляем сообщение с клавиатурой
        await paginator.generate(format_text="Список групп (страница {page} из {pages})")


    @router.callback_query(GroupPaginationCallbackFactory.filter())
    async def paginate_groups(callback_query: CallbackQuery, callback_data: GroupPaginationCallbackFactory, group_query: GroupQuery):
        page = callback_data.page

        paginator = Paginator(
            callback_query,
            items=await group_query.get_groups_paginated(limit=GROUP_PER_PAGE, offset=page * GROUP_PER_PAGE),
            total_count=await group_query.get_total_groups_count(),
            item_renderer=lambda group: template(
                text=f"{group['id']}:{group['name']} {group['chat_id']}",
                callback_data=ToggleGroupCallbackFactory(group_id=group['chat_id'])
            ),
            paginate_callback_factory=GroupPaginationCallbackFactory,
            items_per_page=GROUP_PER_PAGE,
            page=page
        )

        # Обновляем сообщение с клавиатурой
        await paginator.generate(format_text="Список групп (страница {page} из {pages})")


    ##################################
    Необходимые запросы к базе данных
    ##################################

    class GroupQuery(Query):
        async def get_groups_paginated(self, limit: int, offset: int) -> list[Optional[dict]]:
            result = await self.session.execute(
                select(Group).offset(offset).limit(limit)
            )
            groups = [group.to_dict for group in result.scalars().all()]
            return groups

        async def get_total_groups_count(self) -> int:
            result = await self.session.execute(
                select(func.count()).select_from(Group)
            )
            return result.scalar()
    """

    def __init__(
        self,
        telegram_object: Message | CallbackQuery,
        *,
        items: List[Any],  # Уже загруженные данные для текущей страницы
        total_count: int,  # Общее количество элементов
        item_renderer: Callable[[Any], dict],  # Функция для рендера кнопки из элемента
        paginate_callback_factory: Type[CallbackData],  # Фабрика для callback_data
        items_per_page: int = 5,  # Количество элементов на страницу
        page: int = 0,  # Текущая страница
        data_callback: Optional[dict] = None
    ) -> None:
        self.telegram_object = telegram_object

        self.items = items
        self.total_count = total_count
        self.item_renderer = item_renderer
        self.callback_factory = paginate_callback_factory
        self.items_per_page = items_per_page
        self.page = page
        self.data_callback = data_callback if data_callback else {}

    async def generate_answer(self, format_text: str, inline: bool = True) -> None:
        """
        Генерирует ответ пагинации.

        :return: None
        """
        total_pages = (self.total_count - 1) // self.items_per_page + 1

        buttons = [
            self.item_renderer(item)
            for item in self.items
        ] + [
            [
                template(
                    text="⬅️ Назад", callback_data=self.callback_factory(page=self.page - 1, **self.data_callback).pack()
                ) if self.page > 0 else None,
                template(
                    text="Вперед ➡️", callback_data=self.callback_factory(page=self.page + 1, **self.data_callback).pack()
                ) if self.page < total_pages - 1 else None,
            ]
        ]

        text = format_text.format(page=self.page + 1, pages=total_pages, total_count=self.total_count)
        keyboard = generate_keyboard(buttons, inline=inline)

        if isinstance(self.telegram_object, Message):
            await self.telegram_object.answer(text, reply_markup=keyboard)
        elif isinstance(self.telegram_object, CallbackQuery):
            await self.telegram_object.message.edit_text(text, reply_markup=keyboard)
            await self.telegram_object.answer()
