import httpx
from parsers.base import BaseParser, Vacancy

CITY_AREA_IDS = {
    "Алматы": 159,
    "Астана": 160,
    "Шымкент": 4088,
    "Другой город": 40,
}

HH_API_URL = "https://api.hh.ru/vacancies"


class HHParser(BaseParser):
    async def parse(self, query: str, city: str = "Другой город", limit: int = 20) -> list[Vacancy]:
        area_id = CITY_AREA_IDS.get(city, 40)
        params = {"text": query, "area": area_id, "per_page": min(limit, 50)}

        async with httpx.AsyncClient(timeout=15, headers={"User-Agent": "job-bot/1.0"}) as client:
            resp = await client.get(HH_API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        vacancies = []
        for item in data.get("items", []):
            salary = item.get("salary") or {}
            vacancies.append(Vacancy(
                external_id=str(item["id"]),
                title=item.get("name", ""),
                company=(item.get("employer") or {}).get("name"),
                salary_from=salary.get("from"),
                salary_to=salary.get("to"),
                currency=salary.get("currency") or "KZT",
                city=(item.get("area") or {}).get("name") or city,
                description_raw=(item.get("snippet") or {}).get("responsibility"),
                url=item.get("alternate_url"),
            ))
        return vacancies