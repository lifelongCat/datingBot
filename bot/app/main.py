import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from config import settings
from fsm import router as fsm_router
from handlers import router as handlers_router
from middlewares import ErrorMiddleware


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    await bot.set_my_commands([
        BotCommand(command='start', description='Начать заполнение Вашей анкеты'),
        BotCommand(command='referal_link', description='Получить реферальную ссылку'),
        BotCommand(command='profile', description='Посмотреть свою анкету'),
        BotCommand(
            command='set_avatar',
            description=(
                'Изменение Вашего пользователя, можно отправить ТОЛЬКО '
                'фотографию, прикреплённую к команде'
            )
        ),
        BotCommand(command='find_people', description='Найти людей'),
        BotCommand(
            command='unchecked_likes',
            description='Вывести непросмотренные лайки от пользователей'
        ),
    ])

    dp.include_routers(handlers_router, fsm_router)
    dp.message.outer_middleware(ErrorMiddleware())

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
