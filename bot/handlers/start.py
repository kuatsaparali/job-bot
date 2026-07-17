from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from bot.keyboards import get_main_menu

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"Привет, {message.from_user.full_name}! Я помогу тебе найти идеальную работу с помощью ИИ умного поиска.\n\n"
        "Нажми кнопку ниже, чтобы начать поиск.",
        reply_markup=get_main_menu()
    )