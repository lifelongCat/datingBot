from collections.abc import Generator
from datetime import datetime
from typing import BinaryIO

import pytz
from minio import S3Error
from sqlalchemy import insert, select, text, update

from app.config import settings
from app.database import async_session_maker, minio_client
from app.models import User, UserInteraction, UserRating
from app.schemas import SUser


class PostgresRepository:
    @staticmethod
    async def find_user_or_none(telegram_id: int) -> SUser | None:
        async with async_session_maker() as session:
            query = select(User.__table__.columns).filter_by(telegram_id=telegram_id)
            result = await session.execute(query)
            user = result.mappings().one_or_none()
            return SUser(**user) if user else None

    @staticmethod
    async def create_user(**values) -> None:
        async with async_session_maker() as session:
            query = insert(User).values(
                last_activity=datetime.now(pytz.UTC).replace(tzinfo=None), **values
            )
            await session.execute(query)
            query = insert(UserRating).values(telegram_id=values['telegram_id'])
            await session.execute(query)
            await session.commit()

    @staticmethod
    async def update_user(telegram_id: int, **values) -> None:
        async with async_session_maker() as session:
            query = update(User).where(User.telegram_id == telegram_id).values(**values)
            await session.execute(query)
            await session.commit()

    @staticmethod
    async def like_user(requester_telegram_id: int, responser_telegram_id: int) -> None:
        async with async_session_maker() as session:
            query = insert(UserInteraction).values(
                requester_telegram_id=requester_telegram_id,
                responser_telegram_id=responser_telegram_id,
                is_like=True,
                is_checked=False
            )
            await session.execute(query)
            await session.commit()

    @staticmethod
    async def skip_user(requester_telegram_id: int, responser_telegram_id: int) -> None:
        async with async_session_maker() as session:
            query = insert(UserInteraction).values(
                requester_telegram_id=requester_telegram_id,
                responser_telegram_id=responser_telegram_id,
                is_like=False
            )
            await session.execute(query)
            await session.commit()

    @staticmethod
    async def find_people(telegram_id: int) -> list[int]:
        async with async_session_maker() as session:
            query = text(f'''
                SELECT
                    u.telegram_id,
                    abs(rating - (
                        SELECT rating
                        FROM user_ratings
                        WHERE telegram_id = {telegram_id}
                    )) as rating_diff,
                    abs(age - age_preferences) as age_diff,
                    gender != gender_preferences as gender_diff
                FROM user_ratings ur
                JOIN users u ON u.telegram_id = ur.telegram_id
                WHERE u.telegram_id NOT IN (
                    SELECT responser_telegram_id
                    FROM user_interactions
                    WHERE requester_telegram_id = {telegram_id}
                ) AND u.telegram_id != {telegram_id}
                ORDER BY rating_diff asc, gender_diff asc, age_diff asc
                LIMIT 10
                ;
            ''')
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def find_unchecked_likes(telegram_id: int) -> int | None:
        async with async_session_maker() as session:
            query = text(f'''
                SELECT requester_telegram_id
                FROM user_interactions
                WHERE responser_telegram_id = {telegram_id} AND is_checked = False
                LIMIT 1
                ;
            ''')
            result = await session.execute(query)
            finded_telegram_id = result.scalar()
            if not finded_telegram_id:
                return None
            query = text(f'''
                UPDATE user_interactions
                SET is_checked = True
                WHERE requester_telegram_id = {finded_telegram_id}
                    AND responser_telegram_id = {telegram_id}
            ''')
            await session.execute(query)
            await session.commit()
            return finded_telegram_id


class MinIORepository:
    @staticmethod
    def upload_file(filename: str, filesize: int, file: BinaryIO) -> None:
        minio_client.put_object(
            bucket_name=settings.MINIO_BUCKET,
            object_name=filename,
            length=filesize,
            data=file
        )

    @staticmethod
    def download_file(filename: str) -> Generator[bytes]:
        filesize = minio_client.stat_object(settings.MINIO_BUCKET, filename).size
        offset = 0
        while True:
            response = minio_client.get_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=filename,
                offset=offset,
                length=2048
            )
            yield response.read()
            offset = offset + 2048
            if offset >= filesize:
                break

    @staticmethod
    def is_exists(filename: str) -> bool:
        try:
            minio_client.stat_object(settings.MINIO_BUCKET, filename)
            return True
        except S3Error:
            pass
        return False
