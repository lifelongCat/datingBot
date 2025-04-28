from typing import Optional

from pydantic import BaseModel


class SUser(BaseModel):
    telegram_id: int
    gender: str
    age: int
    city: str
    interests: str
    gender_preferences: str
    age_preferences: int
    city_preferences: str
    interests_preferences: str


class SUpdateUser(BaseModel):
    gender: Optional[str] = ''
    age: Optional[int] = 0
    city: Optional[str] = ''
    interests: Optional[str] = ''
    gender_preferences: Optional[str] = ''
    age_preferences: Optional[int] = 0
    city_preferences: Optional[str] = ''
    interests_preferences: Optional[str] = ''
