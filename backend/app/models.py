from datetime import datetime
from typing import Annotated
from uuid import UUID

from sqlalchemy import (BigInteger, DateTime, ForeignKey, String,
                        UniqueConstraint, text)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

MAX_TEXT_LENGTH = 150
unique_name = Annotated[str, mapped_column(String(MAX_TEXT_LENGTH), unique=True)]


class User(Base):
    __tablename__ = 'users'

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    age: Mapped[int]
    gender: Mapped[str]
    interests: Mapped[str]
    city: Mapped[str]
    age_preferences: Mapped[int]
    gender_preferences: Mapped[str]
    interests_preferences: Mapped[str]
    city_preferences: Mapped[str]
    last_activity: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    referal_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id"), nullable=True
    )


class UserInteraction(Base):
    __tablename__ = 'user_interactions'

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text('uuid_generate_v4()'))
    requester_telegram_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"))
    responser_telegram_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"))
    is_like: Mapped[bool]
    # only for likes
    is_checked: Mapped[bool] = mapped_column(nullable=True)
    UniqueConstraint("requester_telegram_id", "responser_telegram_id")


class UserRating(Base):
    __tablename__ = 'user_ratings'

    telegram_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id"), primary_key=True
    )
    rating: Mapped[float] = mapped_column(server_default='0')
