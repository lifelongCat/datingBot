from contextlib import suppress
from inspect import cleandoc

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, PhotoSize
from aiogram.utils.deep_linking import create_start_link
from http_requests import HTTPRequests
from keyboards import (UserEditCallbackFactory, UserInteractionCallbackFactory,
                       get_gender_choice_keyboard,
                       get_user_interaction_keyboard)
from states import RegisterEditForm
from utils import show_user_profile

router = Router()


@router.message(StateFilter(None), CommandStart())
@router.message(StateFilter(None), CommandStart(deep_link=True, deep_link_encoded=True))
async def cmd_start(message: Message, state: FSMContext, command: CommandObject):
    await HTTPRequests.get(
        telegram_id=str(message.from_user.id),
        url='/check_is_registered'
    )
    referal = (await message.bot.get_chat_member(
        chat_id=int(command.args),
        user_id=int(command.args)
    )).user if command.args else None
    await message.answer(
        text=cleandoc(f'''
            Начата регистрация нового аккаунта!
            {
                (
                    f"Ваш реферал: <a href='https://t.me/{referal.username}'>"
                    f"{referal.first_name or ''} {referal.last_name or ''}]</a>"
                )
                if referal else ""
            }
            Для начала, пожалуйста, укажите ваш пол:
        '''),
        parse_mode=ParseMode.HTML,
        reply_markup=get_gender_choice_keyboard()
    )
    await state.set_data({})
    await state.update_data({'referal_id': command.args, 'action': 'create'})
    await state.set_state(RegisterEditForm.gender)


@router.message(StateFilter(None), Command('referal_link'))
async def cmd_referal_link(message: Message):
    link = await create_start_link(message.bot, str(message.from_user.id), encode=True)
    await message.answer(f'Ваша реферальная ссылка: {link}')


@router.message(StateFilter(None), Command('profile'))
async def cmd_get_profile(message: Message):
    await show_user_profile(
        bot=message.bot,
        message=message,
        telegram_id=str(message.from_user.id),
        is_me=True
    )


@router.message(StateFilter(None), Command('set_avatar'), F.photo[-1].as_('largest_photo'))
async def cmd_handle_photo(message: Message, largest_photo: PhotoSize):
    file = await message.bot.download(largest_photo)
    await HTTPRequests.set_avatar(
        telegram_id=str(message.from_user.id),
        files={'file': (f'avatar_{message.from_user.id}.png', file, 'multipart/form-data')}
    )
    await message.answer('Ваш аватар успешно изменён!')


@router.callback_query(UserEditCallbackFactory.filter())
async def callbacks_user_edit(
    callback: CallbackQuery,
    callback_data: UserEditCallbackFactory,
    state: FSMContext
):
    await state.set_data({})
    await state.update_data(action='edit')
    match callback_data.field:
        case 'gender':
            await callback.message.answer(
                'Пожалуйста, укажите ваш новый пол:',
                reply_markup=get_gender_choice_keyboard()
            )
            await state.set_state(RegisterEditForm.gender)
        case 'age':
            await callback.message.answer('Пожалуйста, укажите ваш новый возраст:')
            await state.set_state(RegisterEditForm.age)
        case 'city':
            await callback.message.answer('Пожалуйста, укажите ваш новый город:')
            await state.set_state(RegisterEditForm.city)
        case 'interests':
            await callback.message.answer('Пожалуйста, укажите ваши новые интересы:')
            await state.set_state(RegisterEditForm.interests)
        case 'gender_preferences':
            await callback.message.answer(
                'Пожалуйста, укажите ваши новые предпочтения в поле:',
                reply_markup=get_gender_choice_keyboard()
            )
            await state.set_state(RegisterEditForm.gender_preferences)
        case 'age_preferences':
            await callback.message.answer('Пожалуйста, укажите ваши новые предпочтения в возрасте:')
            await state.set_state(RegisterEditForm.age_preferences)
        case 'city_preferences':
            await callback.message.answer('Пожалуйста, укажите ваш новые предпочтения в городе:')
            await state.set_state(RegisterEditForm.city_preferences)
        case 'interests_preferences':
            await callback.message.answer('Пожалуйста, укажите ваш новые предпочтения в интересах:')
            await state.set_state(RegisterEditForm.interests_preferences)
    await callback.answer()


@router.message(StateFilter(None), Command('find_people'))
async def cmd_find_people(message: Message):
    await show_user_profile(
        bot=message.bot,
        message=message,
        telegram_id=str(message.from_user.id),
        is_find=True
    )


@router.message(StateFilter(None), Command('unchecked_likes'))
async def cmd_unchecked_likes(message: Message):
    await show_user_profile(
        bot=message.bot,
        message=message,
        telegram_id=str(message.from_user.id)
    )


@router.callback_query(UserInteractionCallbackFactory.filter())
async def callbacks_user_interaction(
    callback: CallbackQuery,
    callback_data: UserInteractionCallbackFactory
):
    await callback.answer()
    match callback_data.action:
        case 'like':
            with suppress(TelegramBadRequest):
                await callback.message.edit_caption(
                    caption=(callback.message.caption if callback.message.caption else callback.message.text) + '\n Вы лайкнули эту анкету!',
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=get_user_interaction_keyboard(callback_data.telegram_id)
                )
            await HTTPRequests.post(
                telegram_id=str(callback.from_user.id),
                url=f'/like/{callback_data.telegram_id}'
            )
            await callback.message.bot.send_message(
                chat_id=callback_data.telegram_id,
                text='Ваш профиль кому-то понравился!'
            )
            await show_user_profile(
                bot=callback.message.bot,
                message=callback.message,
                telegram_id=str(callback.from_user.id),
                is_find=True
            )
        case 'skip':
            await HTTPRequests.post(
                telegram_id=str(callback.from_user.id),
                url=f'/skip/{callback_data.telegram_id}'
            )
            await show_user_profile(
                bot=callback.message.bot,
                message=callback.message,
                telegram_id=str(callback.from_user.id),
                is_find=True
            )
