from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PostgreSQL settings
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # MinIO settings
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_ENDPOINT: str
    MINIO_BUCKET: str
    MINIO_SECURE: bool

    # Redis settings
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_USER: str
    REDIS_PASSWORD: str

    # RabbitMQ settings
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_DEFAULT_USER: str
    RABBITMQ_DEFAULT_PASS: str

    @property
    def POSTGRES_URL(self):
        return (f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@'
                f'{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}')

    @property
    def RABBITMQ_URL(self):
        return (f'amqp://{self.RABBITMQ_DEFAULT_USER}:{self.RABBITMQ_DEFAULT_PASS}@'
                f'{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/')

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


settings = Settings()
