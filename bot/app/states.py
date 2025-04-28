from aiogram.fsm.state import State, StatesGroup


class RegisterEditForm(StatesGroup):
    action = State()
    referal_id = State()
    gender = State()
    age = State()
    city = State()
    interests = State()
    gender_preferences = State()
    age_preferences = State()
    city_preferences = State()
    interests_preferences = State()
