from minio import Minio
from redis.asyncio import Redis
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

sync_engine = create_engine(settings.POSTGRES_URL.replace('asyncpg', 'psycopg'))
async_engine = create_async_engine(settings.POSTGRES_URL)
sync_session_maker = sessionmaker(sync_engine)
async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False)

redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    username=settings.REDIS_USER,
    password=settings.REDIS_PASSWORD,
    decode_responses=True
)

minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ROOT_USER,
    secret_key=settings.MINIO_ROOT_PASSWORD,
    secure=settings.MINIO_SECURE
)
if not minio_client.bucket_exists(settings.MINIO_BUCKET):
    minio_client.make_bucket(settings.MINIO_BUCKET)


class Base(DeclarativeBase):
    pass
