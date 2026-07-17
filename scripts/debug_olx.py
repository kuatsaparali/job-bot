import asyncio
import re
from urllib.parse import quote
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


async def debug():
    query = "Официант"
    city = "Алматы"
    search_text = f"{query} {city}"
    slug = quote(search_text.replace(" ", "-"))
    search_url = f"https://www.olx.kz/rabota/q-{slug}/"

    print(f"Открываю: {search_url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            response = await page.goto(search_url, timeout=20000)
            print(f"HTTP статус: {response.status if response else 'нет ответа'}")

            await page.wait_for_selector('[data-testid="l-card"]', timeout=10000)
            print("✅ Карточки вакансий найдены на странице!")

            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")
            cards = soup.find_all(attrs={"data-testid": "l-card"})
            print(f"Найдено карточек через селектор: {len(cards)}")

            if cards:
                first = cards[0]
                title_elem = first.find("h6")
                link_elem = first.find("a", href=re.compile(r"/obyavlenie/|/d/"))
                print(f"h6 найден: {title_elem is not None} -> {title_elem.text.strip() if title_elem else None}")
                print(f"ссылка найдена: {link_elem is not None} -> {link_elem.get('href') if link_elem else None}")

                with open("debug_olx_first_card.html", "w", encoding="utf-8") as f:
                    f.write(first.prettify())
                print("Полный HTML первой карточки сохранён в debug_olx_first_card.html — открой и покажи мне")

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print("Сохраняю скриншот и HTML для диагностики...")
            await page.screenshot(path="debug_olx_screenshot.png", full_page=True)
            html = await page.content()
            with open("debug_olx_page.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("Смотри debug_olx_screenshot.png и debug_olx_page.html в корне проекта")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug())