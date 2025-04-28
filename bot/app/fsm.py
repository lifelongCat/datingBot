import logging

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from http_requests import HTTPRequests
from keyboards import get_gender_choice_keyboard
from states import RegisterEditForm

router = Router()


@router.message(RegisterEditForm.gender, F.text.in_(['Мужской', 'Женский']))
async def gender_chosen(message: Message, state: FSMContext):
    await state.update_data(gender=message.text.lower())
    if await state.get_value('action') == 'edit':
        await message.answer(
            'Принято',
            reply_markup=ReplyKeyboardRemove()
        )
        await confirm_edit(message=message, state=state)
    if await state.get_value('action') == 'create':
        await message.answer(
            'Хорошо, теперь, пожалуйста, укажите ваш возраст:',
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(RegisterEditForm.age)


@router.message(RegisterEditForm.gender)
async def gender_chosen_incorrectly(message: Message):
    await message.answer(
        text='Пожалуйста, укажите корректный пол:',
        reply_markup=get_gender_choice_keyboard()
    )


@router.message(RegisterEditForm.age)
async def age_chosen(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 0 or int(message.text) > 150:
        await message.answer('Пожалуйста, укажите корректный возраст от 0 до 150')
        return
    await state.update_data(age=message.text.lower())
    if await state.get_value('action') == 'edit':
        await confirm_edit(message=message, state=state)
    if await state.get_value('action') == 'create':
        await message.answer('Хорошо, теперь, пожалуйста, укажите ваш город:')
        await state.set_state(RegisterEditForm.city)


@router.message(RegisterEditForm.city)
async def city_chosen(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    if await state.get_value('action') == 'edit':
        await confirm_edit(message=message, state=state)
    if await state.get_value('action') == 'create':
        await message.answer('Хорошо, теперь, пожалуйста, укажите ваши интересы:')
        await state.set_state(RegisterEditForm.interests)


@router.message(RegisterEditForm.interests)
async def interests_chosen(message: Message, state: FSMContext):
    await state.update_data(interests=message.text)
    if await state.get_value('action') == 'edit':
        await confirm_edit(message=message, state=state)
    if await state.get_value('action') == 'create':
        await message.answer(
            'Хорошо, теперь, пожалуйста, укажите ваши предпочтения в поле:',
            reply_markup=get_gender_choice_keyboard()
        )
        await state.set_state(RegisterEditForm.gender_preferences)


@router.message(RegisterEditForm.gender_preferences, F.text.in_(['Мужской', 'Женский']))
async def gender_preferences_chosen(message: Message, state: FSMContext):
    await state.update_data(gender_preferences=message.text.lower())
    if await state.get_value('action') == 'edit':
        await message.answer(
            'Принято',
            reply_markup=ReplyKeyboardRemove()
        )
        await confirm_edit(message=message, state=state)
    if await state.get_value('action') == 'create':
        await message.answer(
            'Хорошо, теперь, пожалуйста, укажите ваш предпочтения в возрасте:',
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(RegisterEditForm.age_preferences)


@router.message(RegisterEditForm.gender_preferences)
async def gender_preferences_chosen_incorrectly(message: Message):
    await message.answer(
        text='Пожалуйста, укажите корректный пол:',
        reply_markup=get_gender_choice_keyboard()
    )


@router.message(RegisterEditForm.age_preferences)
async def age_preferences_chosen(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 0 or int(message.text) > 150:
        await message.answer('Пожалуйста, укажите корректный возраст от 0 до 150')
        return
    await state.update_data(age_preferences=message.text)
    if await state.get_value('action') == 'edit':
        await confirm_edit(message=message, state=state)
    if await state.get_value('action') == 'create':
        await message.answer('Хорошо, теперь, пожалуйста, укажите ваши предпочтения в городе:')
        await state.set_state(RegisterEditForm.city_preferences)


@router.message(RegisterEditForm.city_preferences)
async def city_preferences_chosen(message: Message, state: FSMContext):
    await state.update_data(city_preferences=message.text)
    if await state.get_value('action') == 'edit':
        await confirm_edit(message=message, state=state)
    if await state.get_value('action') == 'create':
        await message.answer('Хорошо, теперь, пожалуйста, укажите ваши предпочтения в интересах:')
        await state.set_state(RegisterEditForm.interests_preferences)


@router.message(RegisterEditForm.interests_preferences)
async def interests_preferences_chosen(message: Message, state: FSMContext):
    await state.update_data(interests_preferences=message.text)
    if await state.get_value('action') == 'edit':
        await confirm_edit(message=message, state=state)
    if await state.get_value('action') == 'create':
        await confirm_creating(message=message, state=state)


async def confirm_creating(message: Message, state: FSMContext):
    user_data = await state.get_data()
    logging.getLogger().error(user_data)
    await HTTPRequests.post(
        telegram_id=str(message.from_user.id),
        url='/users',
        json={
            'telegram_id': str(message.from_user.id),
            **user_data
        }
    )
    await message.answer('Спасибо, ваши данные сохранены!')
    await state.clear()


async def confirm_edit(message: Message, state: FSMContext):
    user_data = await state.get_data()
    await HTTPRequests.patch(
        telegram_id=str(message.from_user.id),
        url='/users',
        json=user_data
    )
    await message.answer('Спасибо, ваши данные сохранены!')
    await state.clear()


@router.message(StateFilter(None), Command(commands=['cancel']))
@router.message(StateFilter(None), F.text.lower() == 'отмена')
async def cmd_cancel_no_state(message: Message, state: FSMContext):
    await state.set_data({})
    await message.answer(
        text='Нечего отменять',
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(Command(commands=['cancel']))
@router.message(F.text.lower() == 'отмена')
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text='Заполнение анкеты отменено',
        reply_markup=ReplyKeyboardRemove()
    )
