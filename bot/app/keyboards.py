from aiogram.filters.callback_data import CallbackData
from aiogram.types import (InlineKeyboardMarkup, KeyboardButton,
                           ReplyKeyboardMarkup)
from aiogram.utils.keyboard import InlineKeyboardBuilder


class UserInteractionCallbackFactory(CallbackData, prefix="user_interaction"):
    action: str
    telegram_id: int


class UserEditCallbackFactory(CallbackData, prefix="user_edit"):
    field: str


def get_gender_choice_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=item) for item in ('Мужской', 'Женский')]],
        resize_keyboard=True
    )


def get_user_edit_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Пол',
        callback_data=UserEditCallbackFactory(field='gender')
    )
    builder.button(
        text='Возраст',
        callback_data=UserEditCallbackFactory(field='age')
    )
    builder.button(
        text='Город',
        callback_data=UserEditCallbackFactory(field='city')
    )
    builder.button(
        text='Интересы',
        callback_data=UserEditCallbackFactory(field='interests')
    )
    builder.button(
        text='Предпочтения в поле',
        callback_data=UserEditCallbackFactory(field='gender_preferences')
    )
    builder.button(
        text='Предпочтения в возрасте',
        callback_data=UserEditCallbackFactory(field='age_preferences')
    )
    builder.button(
        text='Предпочтения в городе',
        callback_data=UserEditCallbackFactory(field='city_preferences')
    )
    builder.button(
        text='Предпочтения в интересах',
        callback_data=UserEditCallbackFactory(field='interests_preferences')
    )
    builder.adjust(1)
    return builder.as_markup()


def get_user_interaction_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Лайкнуть',
        callback_data=UserInteractionCallbackFactory(
            action='like',
            telegram_id=telegram_id
        )
    )
    builder.button(
        text='Пропустить',
        callback_data=UserInteractionCallbackFactory(
            action='skip',
            telegram_id=telegram_id
        )
    )
    builder.adjust(2)
    return builder.as_markup()
