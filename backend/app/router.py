from fastapi import APIRouter, File, Request, UploadFile, status
from fastapi.exceptions import HTTPException
from starlette.responses import StreamingResponse

from app.database import redis_client
from app.repositories import MinIORepository, PostgresRepository
from app.schemas import SUpdateUser, SUser

router = APIRouter()


@router.get('/check_is_registered', status_code=status.HTTP_204_NO_CONTENT)
async def check_is_registered(request: Request) -> None:
    if await PostgresRepository.find_user_or_none(request.state.telegram_id):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            'Пользователь с данным telegram_id уже зарегистрирован!'
        )


@router.get('/users/{telegram_id}', status_code=status.HTTP_200_OK)
async def get_user(telegram_id: int) -> SUser:
    user = await PostgresRepository.find_user_or_none(telegram_id)
    if not user:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            'Пользователь с данным telegram_id НЕ найден!'
        )
    return user


@router.post('/users', status_code=status.HTTP_201_CREATED)
async def register_user(user: SUser) -> None:
    await PostgresRepository.create_user(**user.model_dump())


@router.patch('/users', status_code=status.HTTP_204_NO_CONTENT)
async def update_user(request: Request, user: SUpdateUser) -> None:
    await PostgresRepository.update_user(
        request.state.telegram_id, **user.model_dump(exclude_unset=True)
    )


@router.post('/set_avatar', status_code=status.HTTP_204_NO_CONTENT)
def set_avatar(file: UploadFile = File(...)) -> None:
    MinIORepository.upload_file(
        filename=file.filename,
        filesize=file.size,
        file=file.file
    )


@router.get('/get_avatar/{telegram_id}', status_code=status.HTTP_200_OK)
def get_avatar(telegram_id: int):
    if not MinIORepository.is_exists(f'avatar_{telegram_id}.png'):
        return None
    return StreamingResponse(
        content=MinIORepository.download_file(f'avatar_{telegram_id}.png'),
        media_type='application/octet-stream'
    )


@router.post('/like/{telegram_id}', status_code=status.HTTP_204_NO_CONTENT)
async def like_user(request: Request, telegram_id: int) -> None:
    await PostgresRepository.like_user(request.state.telegram_id, telegram_id)


@router.post('/skip/{telegram_id}', status_code=status.HTTP_204_NO_CONTENT)
async def skip_user(request: Request, telegram_id: int) -> None:
    await PostgresRepository.skip_user(request.state.telegram_id, telegram_id)


@router.get('/unchecked_likes')
async def find_unchecked_likes(request: Request) -> SUser:
    telegram_id = await PostgresRepository.find_unchecked_likes(request.state.telegram_id)
    if not telegram_id:
        raise HTTPException(status.HTTP_418_IM_A_TEAPOT, 'Просмотрены все пользователи')
    return await PostgresRepository.find_user_or_none(telegram_id)


@router.get('/find_people', status_code=status.HTTP_200_OK)
async def find_people(request: Request) -> SUser | None:
    telegram_id = request.state.telegram_id
    if not await redis_client.llen(telegram_id):
        new_users = await PostgresRepository.find_people(telegram_id)
        if not new_users:
            raise HTTPException(status.HTTP_418_IM_A_TEAPOT, 'Просмотрены все пользователи')
        for user_id in await PostgresRepository.find_people(telegram_id):
            await redis_client.rpush(telegram_id, user_id)
    return await PostgresRepository.find_user_or_none(int(await redis_client.lpop(telegram_id)))
