import asyncpg
from config import config

_pool = None

async def get_db_pool():
    global _pool
    if _pool is None:
        # Заменяем префикс, если пользователь случайно указал postgresql:// вместо postgres://
        db_url = config.DATABASE_URL.replace("postgresql://", "postgres://")
        _pool = await asyncpg.create_pool(db_url)
    return _pool

async def close_db_pool():
    global _pool
    if _pool:
        await _pool.close()