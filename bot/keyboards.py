from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from categories import CATEGORIES, CUSTOM_CODE, CUSTOM_LABEL
from cities import CITIES, OTHER_CITY_LABEL


def get_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔍 Найти работу")]],
        resize_keyboard=True,
    )


def get_cities_keyboard() -> ReplyKeyboardMarkup:
    rows = []
    for i in range(0, len(CITIES), 2):
        pair = CITIES[i:i + 2]
        rows.append([KeyboardButton(text=c) for c in pair])
    rows.append([KeyboardButton(text=OTHER_CITY_LABEL)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def get_categories_keyboard(selected: set[str]) -> InlineKeyboardMarkup:
    """
    Мультивыбор: выбранные пункты помечаются галочкой.
    Нажатие на пункт не закрывает клавиатуру — переключает чекбокс.
    """
    rows = []
    for code, label in CATEGORIES:
        prefix = "✅ " if code in selected else ""
        rows.append([InlineKeyboardButton(text=f"{prefix}{label}", callback_data=f"cat:{code}")])

    custom_prefix = "✅ " if CUSTOM_CODE in selected else ""
    rows.append([InlineKeyboardButton(text=f"{custom_prefix}{CUSTOM_LABEL}", callback_data=f"cat:{CUSTOM_CODE}")])

    done_label = f"🚀 Готово, искать ({len(selected)})" if selected else "🚀 Готово"
    rows.append([InlineKeyboardButton(text=done_label, callback_data="cat:done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_stop_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🛑 Стоп")]],
        resize_keyboard=True,
    )


def get_after_stop_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔍 Искать ещё")]],
        resize_keyboard=True,
    )