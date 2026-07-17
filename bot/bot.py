import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import config
from db.connection import get_db_pool, close_db_pool
from bot.handlers import start, search

logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализация пула БД при старте
    await get_db_pool()
    
    bot = Bot(token=config.BOT_TOKEN.get_secret_value())
    dp = Dispatcher()
    
    # Регистрируем наши роутеры хендлеров
    dp.include_routers(start.router, search.router)
    
    try:
        print("Бот успешно запущен!")
        await dp.start_polling(bot)
    finally:
        await close_db_pool()

if __name__ == "__main__":
    asyncio.run(main())