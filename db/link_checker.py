"""
Проверяет вакансии старше 3 дней: если ссылка больше не открывается
(404, редирект на "вакансия снята" и т.д.) — помечает is_active = FALSE.
Ничего физически не удаляет из базы (полезно для истории/статистики),
просто исключает мёртвые вакансии из будущих ответов бота.

Запуск вручную: python -m db.link_checker
Продовый режим: раз в сутки через cron / systemd timer / APScheduler.
"""
import asyncio
import httpx
from db.connection import get_db_pool, close_db_pool

BATCH_SIZE = 100
STALE_AFTER_DAYS = 3
RECHECK_EVERY_HOURS = 24


async def check_one(client: httpx.AsyncClient, url: str) -> bool:
    """True = вакансия ещё жива."""
    try:
        resp = await client.head(url, follow_redirects=True, timeout=10)
        if resp.status_code >= 400:
            resp = await client.get(url, follow_redirects=True, timeout=10)
        return resp.status_code < 400
    except httpx.HTTPError:
        return False


async def run():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"""
            SELECT id, url FROM vacancies
            WHERE is_active = TRUE
              AND created_at < now() - interval '{STALE_AFTER_DAYS} days'
              AND (last_checked_at IS NULL OR last_checked_at < now() - interval '{RECHECK_EVERY_HOURS} hours')
            LIMIT {BATCH_SIZE}
            """
        )

    if not rows:
        print("Нечего проверять.")
        return

    async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}) as client:
        for row in rows:
            alive = await check_one(client, row["url"])
            async with pool.acquire() as conn:
                if alive:
                    await conn.execute(
                        "UPDATE vacancies SET last_checked_at = now() WHERE id = $1", row["id"]
                    )
                else:
                    await conn.execute(
                        "UPDATE vacancies SET is_active = FALSE, last_checked_at = now() WHERE id = $1",
                        row["id"],
                    )
                    print(f"Деактивирована (устарела): {row['url']}")

    print(f"Проверено {len(rows)} вакансий.")


if __name__ == "__main__":
    asyncio.run(run())
    asyncio.run(close_db_pool())