from inspect import cleandoc

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile, Message
from http_requests import HTTPRequests
from keyboards import get_user_edit_keyboard, get_user_interaction_keyboard


async def show_user_profile(
    bot: Bot,
    message: Message,
    telegram_id: str,
    is_me: bool = False,
    is_find: bool = False
):
    user_profile = await HTTPRequests.get(
        telegram_id=telegram_id,
        url=f'/users/{telegram_id}' if is_me else '/find_people' if is_find else '/unchecked_likes'
    )
    avatar = await HTTPRequests.get_avatar(
        telegram_id=telegram_id if is_me else str(user_profile["telegram_id"])
    )
    user = (await bot.get_chat_member(
        chat_id=user_profile['telegram_id'],
        user_id=user_profile['telegram_id']
    )).user
    user_description = cleandoc(f'''
        Имя: <a href='https://t.me/{user.username}'>{user.first_name or ''} {user.last_name or ''}</a>
        Пол: {user_profile['gender']}
        Возраст: {user_profile['age']}
        Город: {user_profile['city']}
        Интересы: {user_profile['interests']}

        Предпочтения в поле: {user_profile['gender']}
        Предпочтения в возрасте: {user_profile['age']}
        Предпочтения в городе: {user_profile['city']}
        Предпочтения в интересах: {user_profile['interests']}

        {'Изменить профиль:' if is_me else ''}
    ''')
    if not avatar:
        await message.answer(
            text=user_description,
            parse_mode=ParseMode.HTML,
            reply_markup=(
                get_user_edit_keyboard() if is_me
                else get_user_interaction_keyboard(user_profile['telegram_id'])
            )
        )
    else:
        await message.answer_photo(
            photo=BufferedInputFile(
                avatar.read(),
                filename='avatar.png'
            ),
            caption=user_description,
            parse_mode=ParseMode.HTML,
            reply_markup=(
                get_user_edit_keyboard() if is_me
                else get_user_interaction_keyboard(user_profile['telegram_id'])
            )
        )
