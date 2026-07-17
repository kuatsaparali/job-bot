"""
Парсер OLX.kz — публичного API нет, поэтому используем Playwright.
URL-схема раздела "Работа": https://www.olx.kz/rabota/q-<запрос>/
Города как отдельного сегмента пути НЕТ (в отличие от других разделов OLX) —
поэтому город добавляем прямо в текст поискового запроса.
ВНИМАНИЕ: скрапинг HTML хрупкий — если OLX поменяет вёрстку, селекторы
(data-testid="l-card", тег h4, /obyavlenie/) придётся поправить.
Сверено с реальной карточкой 17.07.2026 — см. scripts/debug_olx.py для повторной проверки.
"""
import re
from urllib.parse import quote
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser
from parsers.base import BaseParser, Vacancy

SALARY_RE = re.compile(r"([\d\s]+)\s*-\s*([\d\s]+)\s*₸|([\d\s]+)\s*₸")


def _parse_salary(text: str | None) -> tuple[int | None, int | None]:
    """'600 000 - 700 000 ₸ / за месяц' -> (600000, 700000). Одно число -> (X, X)."""
    if not text:
        return None, None
    match = SALARY_RE.search(text)
    if not match:
        return None, None
    if match.group(1) and match.group(2):
        low = int(match.group(1).replace(" ", "").replace("\xa0", ""))
        high = int(match.group(2).replace(" ", "").replace("\xa0", ""))
        return low, high
    if match.group(3):
        value = int(match.group(3).replace(" ", "").replace("\xa0", ""))
        return value, value
    return None, None


def _build_url(query: str, city: str) -> str:
    search_text = query if city == "Другой город" else f"{query} {city}"
    slug = quote(search_text.strip().replace(" ", "-"))
    return f"https://www.olx.kz/rabota/q-{slug}/"


def _extract_vacancies(html: str, city: str, limit: int) -> list[Vacancy]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all(attrs={"data-testid": "l-card"})

    vacancies = []
    for card in cards[:limit]:
        title_elem = card.find("h4")
        link_elem = card.find("a", href=re.compile(r"/obyavlenie/|/d/"))
        if not title_elem or not link_elem:
            continue

        url = link_elem["href"]
        if not url.startswith("http"):
            url = f"https://www.olx.kz{url}"

        salary_from = salary_to = None
        for p in card.find_all("p"):
            if "₸" in p.text:
                salary_from, salary_to = _parse_salary(p.text)
                break

        city_elem = card.select_one("span.css-jw5wnz") or card.select_one("span.css-pnkc9g")
        found_city = city_elem.get_text(strip=True) if city_elem else city

        vacancies.append(Vacancy(
            external_id=url.rstrip("/").split("-")[-1].replace(".html", ""),
            title=title_elem.text.strip(),
            company="OLX",
            url=url,
            city=found_city,
            salary_from=salary_from,
            salary_to=salary_to,
            currency="KZT",
            description_raw=None,
        ))
    return vacancies


class OLXParser(BaseParser):
    def __init__(self):
        self.base_url = "https://www.olx.kz"

    async def _fetch_one(self, browser: Browser, query: str, city: str, limit: int) -> list[Vacancy]:
        search_url = _build_url(query, city)
        page = await browser.new_page()
        try:
            # domcontentloaded вместо "load" по умолчанию — не ждём фоновые
            # трекеры/рекламу, которые иногда никогда не долетают и вызывают
            # ложные таймауты. Готовность страницы всё равно проверяем через
            # wait_for_selector ниже.
            await page.goto(search_url, timeout=20000, wait_until="domcontentloaded")
            await page.wait_for_selector('[data-testid="l-card"]', timeout=10000)
            content = await page.content()
            return _extract_vacancies(content, city, limit)
        except Exception as e:
            print(f"[OLX] Ошибка для запроса '{query}' ({search_url}): {e}")
            return []
        finally:
            await page.close()

    async def parse(self, query: str, city: str = "Другой город", limit: int = 20) -> list[Vacancy]:
        """Разовый запрос — поднимает свой браузер. Удобно для отладки/одного запроса."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                return await self._fetch_one(browser, query, city, limit)
            finally:
                await browser.close()

    async def parse_many(self, queries: list[str], city: str = "Другой город", limit: int = 20):
        """
        Один браузер на ВЕСЬ список запросов — быстрее и надёжнее, чем
        перезапускать Chromium на каждую категорию по отдельности.
        Yield'ит (query, vacancies) по мере готовности каждого запроса —
        удобно для стриминга результатов в чат.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                for query in queries:
                    vacancies = await self._fetch_one(browser, query, city, limit)
                    yield query, vacancies
            finally:
                await browser.close()