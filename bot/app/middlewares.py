import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class DatingBotException(BaseException):
    pass


class ErrorMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except DatingBotException as e:
            await event.bot.send_message(
                chat_id=event.from_user.id,
                text=str(e)
            )
        except Exception as e:
            logging.getLogger().error(
                f'user_id: {event.from_user.id}, user_text: {event.text}, error: {str(e)}'
            )
        return None
