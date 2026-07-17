from aiogram.fsm.state import State, StatesGroup


class SearchJob(StatesGroup):
    choosing_city = State()
    choosing_categories = State()
    waiting_custom_category = State()
    searching = State()