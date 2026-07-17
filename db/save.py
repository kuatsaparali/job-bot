from db.connection import get_db_pool
from parsers.base import Vacancy
from typing import List, Optional


async def get_or_create_source(conn, source_name: str) -> int:
    return await conn.fetchval(
        "INSERT INTO sources (name) VALUES ($1) ON CONFLICT (name) DO UPDATE SET name=$1 RETURNING id",
        source_name,
    )


async def try_insert_vacancy(source_name: str, vacancy: Vacancy, category: str) -> bool:
    """
    Пытается вставить ОДНУ вакансию.
    Возвращает True, если вакансия новая (стоит отправить пользователю).
    Возвращает False, если вакансия уже есть в базе (дубль — не отправляем повторно).
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        source_id = await get_or_create_source(conn, source_name)
        row = await conn.fetchrow(
            """
            INSERT INTO vacancies
                (source_id, external_id, title, company, description_raw,
                 url, city, salary_from, salary_to, category, is_active, last_checked_at)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10, TRUE, now())
            ON CONFLICT (url) DO NOTHING
            RETURNING id
            """,
            source_id, vacancy.external_id, vacancy.title, vacancy.company,
            vacancy.description_raw, vacancy.url, vacancy.city,
            vacancy.salary_from, vacancy.salary_to, category,
        )
        return row is not None


async def save_vacancies(source_name: str, vacancies: List[Vacancy], category: Optional[str] = None):
    """Пакетная вставка (используется скриптами наполнения базы, без рассылки в чат)."""
    if not vacancies:
        return 0

    pool = await get_db_pool()
    new_count = 0
    async with pool.acquire() as conn:
        source_id = await get_or_create_source(conn, source_name)
        for v in vacancies:
            row = await conn.fetchrow(
                """
                INSERT INTO vacancies
                    (source_id, external_id, title, company, description_raw,
                     url, city, salary_from, salary_to, category, is_active, last_checked_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10, TRUE, now())
                ON CONFLICT (url) DO NOTHING
                RETURNING id
                """,
                source_id, v.external_id, v.title, v.company, v.description_raw,
                v.url, v.city, v.salary_from, v.salary_to, category,
            )
            if row is not None:
                new_count += 1
    return new_count