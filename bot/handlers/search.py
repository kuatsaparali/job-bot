import asyncio
import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from bot.states import SearchJob
from bot.keyboards import (
    get_cities_keyboard, get_categories_keyboard,
    get_stop_keyboard, get_after_stop_keyboard,
)
from categories import CATEGORY_BY_CODE, CUSTOM_CODE
from db.save import try_insert_vacancy
from parsers.hh_parser import HHParser
from parsers.olx_parser import OLXParser

router = Router()

# user_id -> bool. Пока True — поиск продолжается. Стоп-кнопка переключает в False.
active_searches: dict[int, bool] = {}


@router.message(F.text == "🔍 Найти работу")
@router.message(F.text == "🔍 Искать ещё")
async def start_search(message: Message, state: FSMContext):
    await state.set_state(SearchJob.choosing_city)
    await message.answer("Из какого ты города?", reply_markup=get_cities_keyboard())


@router.message(SearchJob.choosing_city)
async def process_city(message: Message, state: FSMContext):
    city = message.text
    await state.update_data(city=city, selected_categories=set())
    await message.answer(
        "Отлично! Теперь выбери одну или несколько вакансий, которые хочешь найти "
        "(можно выбрать сразу несколько, потом нажми «Готово»):",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer("Выбери вакансии:", reply_markup=get_categories_keyboard(set()))
    await state.set_state(SearchJob.choosing_categories)


@router.callback_query(SearchJob.choosing_categories, F.data.startswith("cat:"))
async def toggle_category(callback: CallbackQuery, state: FSMContext):
    code = callback.data.split(":", 1)[1]
    data = await state.get_data()
    selected: set[str] = data.get("selected_categories", set())

    if code == "done":
        if not selected:
            await callback.answer("Выбери хотя бы одну вакансию", show_alert=True)
            return
        await callback.answer()  # отвечаем СРАЗУ, пока токен ещё свежий
        await callback.message.edit_reply_markup(reply_markup=None)
        await run_search(callback.message, state)
        return

    if code == CUSTOM_CODE:
        await callback.message.answer("Напиши название вакансии текстом:")
        await state.set_state(SearchJob.waiting_custom_category)
        await callback.answer()
        return

    # обычный toggle чекбокса
    if code in selected:
        selected.discard(code)
    else:
        selected.add(code)
    await state.update_data(selected_categories=selected)
    await callback.message.edit_reply_markup(reply_markup=get_categories_keyboard(selected))
    await callback.answer()


@router.message(SearchJob.waiting_custom_category)
async def process_custom_category(message: Message, state: FSMContext):
    data = await state.get_data()
    selected: set[str] = data.get("selected_categories", set())
    custom_list: list[str] = data.get("custom_categories", [])

    custom_list.append(message.text.strip())
    selected.add(CUSTOM_CODE)  # чисто для отображения галочки
    await state.update_data(selected_categories=selected, custom_categories=custom_list)

    await state.set_state(SearchJob.choosing_categories)
    await message.answer(
        f"Добавил «{message.text.strip()}». Можешь выбрать ещё или нажать «Готово».",
        reply_markup=get_categories_keyboard(selected),
    )


def _strip_emoji(text: str) -> str:
    """Убирает эмодзи и символы из текста кнопки, оставляя чистый поисковый запрос."""
    cleaned = re.sub(r"[^\w\s\-]", "", text, flags=re.UNICODE)
    return cleaned.strip()


def _resolve_queries(data: dict) -> list[str]:
    codes = data.get("selected_categories", set())
    queries = [_strip_emoji(CATEGORY_BY_CODE[c]) for c in codes if c in CATEGORY_BY_CODE]
    queries += data.get("custom_categories", [])
    return queries


async def run_search(message: Message, state: FSMContext):
    data = await state.get_data()
    city = data.get("city", "Другой город")
    queries = _resolve_queries(data)

    user_id = message.chat.id
    active_searches[user_id] = True
    await state.set_state(SearchJob.searching)
    await message.answer(
        f"⏳ Ищу: {', '.join(queries)} — {city}.\n"
        "Буду присылать вакансии по мере нахождения. Останови в любой момент кнопкой ниже.",
        reply_markup=get_stop_keyboard(),
    )

    # TODO: HH.kz временно отключён — api.hh.ru сейчас блокирует неавторизованные
    # запросы (403 forbidden), см. обсуждение в чате. Верни True, когда решим
    # вопрос с OAuth-токеном или переведём hh_parser.py на Playwright.
    HH_ENABLED = False

    hh = HHParser()
    olx = OLXParser()
    total_sent = 0

    async def _send_found(source_name: str, query: str, found: list):
        nonlocal total_sent
        for vacancy in found:
            if not active_searches.get(user_id):
                return
            is_new = await try_insert_vacancy(source_name, vacancy, category=query)
            if not is_new:
                continue  # уже отправляли раньше — пропускаем, не дублируем
            total_sent += 1
            salary = _format_salary(vacancy.salary_from, vacancy.salary_to, vacancy.currency)
            await message.answer(
                f"💼 <b>{vacancy.title}</b>\n"
                f"🏢 {vacancy.company or '—'}\n"
                f"📍 {vacancy.city or city}\n"
                f"💰 {salary}\n"
                f"🔗 {vacancy.url}",
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            await asyncio.sleep(0.3)  # не спамим телеграм слишком быстро

    # HH — через httpx (быстро, отдельный запрос на категорию — это ок)
    if HH_ENABLED:
        for query in queries:
            if not active_searches.get(user_id):
                break
            try:
                found = await hh.parse(query, city=city, limit=20)
            except Exception as e:
                await message.answer(f"⚠️ Не удалось получить данные с hh.kz по «{query}»: {e}")
                continue
            await _send_found("hh.kz", query, found)

    # OLX — один браузер на ВСЕ категории сразу (parse_many), а не перезапуск
    # Chromium на каждую по отдельности — так быстрее и меньше ложных таймаутов
    if active_searches.get(user_id):
        async for query, found in olx.parse_many(queries, city=city, limit=20):
            if not active_searches.get(user_id):
                break
            await _send_found("olx.kz", query, found)

    stopped_by_user = not active_searches.get(user_id, True)
    active_searches.pop(user_id, None)

    if stopped_by_user:
        await message.answer(f"🛑 Поиск остановлен. Новых вакансий отправлено: {total_sent}.")
    else:
        await message.answer(f"✅ Поиск завершён. Новых вакансий отправлено: {total_sent}.")

    await message.answer(
        "Какие вакансии тебе ещё интересны?",
        reply_markup=get_after_stop_keyboard(),
    )
    await state.set_state(None)


@router.message(SearchJob.searching, F.text == "🛑 Стоп")
async def stop_search(message: Message, state: FSMContext):
    active_searches[message.chat.id] = False
    await message.answer("Останавливаю поиск...", reply_markup=ReplyKeyboardRemove())


def _format_salary(s_from, s_to, currency) -> str:
    if not s_from and not s_to:
        return "З/п не указана"
    if s_from and s_to:
        return f"{s_from}–{s_to} {currency}"
    return f"от {s_from or s_to} {currency}"