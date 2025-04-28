from functools import wraps
from io import BytesIO
from typing import Any, Callable

import httpx
from config import settings
from middlewares import DatingBotException


def async_http_client_decorator(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        async with httpx.AsyncClient() as client:
            try:
                result = await func(client, *args, **kwargs)
                return result
            except httpx.HTTPStatusError as e:
                match e.response.status_code:
                    case 404:
                        raise DatingBotException('Не найдено!')
                    case 409:
                        raise DatingBotException('Ты уже зарегистрирован!')
                    case 418:
                        raise DatingBotException('Все пользователи уже просмотрены!')
                    case _:
                        raise DatingBotException('Ошибка сервера, попробуйте позже...')
    return wrapper


class HTTPRequests:
    @staticmethod
    @async_http_client_decorator
    async def get(
        client: httpx.AsyncClient,
        telegram_id: str,
        url: str
    ) -> dict[str, Any] | None:
        response = await client.get(
            f'{settings.BACKEND_URL}{url}',
            headers={'X-Telegram-ID': telegram_id}
        )
        response.raise_for_status()
        return response.json() if response.text else None

    @staticmethod
    @async_http_client_decorator
    async def post(
        client: httpx.AsyncClient,
        telegram_id: str,
        url: str,
        json: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        response = await client.post(
            f'{settings.BACKEND_URL}{url}',
            json=json if json else {},
            headers={'X-Telegram-ID': telegram_id}
        )
        response.raise_for_status()
        return response.json() if response.text else None

    @staticmethod
    @async_http_client_decorator
    async def patch(
        client: httpx.AsyncClient,
        telegram_id: str,
        url: str,
        json: dict[str, Any]
    ) -> dict[str, Any] | None:
        response = await client.patch(
            f'{settings.BACKEND_URL}{url}',
            json=json,
            headers={'X-Telegram-ID': telegram_id}
        )
        response.raise_for_status()
        return response.json() if response.text else None

    @staticmethod
    @async_http_client_decorator
    async def get_avatar(
        client: httpx.AsyncClient,
        telegram_id: str
    ) -> BytesIO | None:
        response = await client.get(
            f'{settings.BACKEND_URL}/get_avatar/{telegram_id}',
            headers={'X-Telegram-ID': telegram_id}
        )
        response.raise_for_status()
        if response.text == 'null':
            return None

        bio = BytesIO()
        async for chunk in response.aiter_bytes():
            bio.write(chunk)
        bio.seek(0)
        return bio

    @staticmethod
    @async_http_client_decorator
    async def set_avatar(
        client: httpx.AsyncClient,
        telegram_id: str,
        files: dict[str, Any]
    ) -> None:
        response = await client.post(
            f'{settings.BACKEND_URL}/set_avatar',
            files=files,
            headers={'X-Telegram-ID': telegram_id}
        )
        response.raise_for_status()
