import asyncio
from parsers.hh_parser import HHParser
# Импортируй здесь свою функцию сохранения в БД, например:
# from db.save import save_to_db 

async def main():
    parser = HHParser()
    
    # Список городов для парсинга
    cities = [
        {"name": "Шымкент", "id": 40},
        {"name": "Астана", "id": 159},
        {"name": "Алматы", "id": 162}
    ]
    
    # Список профессий
    professions = ["Программист", "Менеджер", "Официант", "Водитель", "Бухгалтер"]
    
    for city in cities:
        for prof in professions:
            print(f"Парсинг: {prof} в городе {city['name']}...")
            vacancies = await parser.parse(prof, area_name=city['name'], area_id=city['id'])
            
            # Вставь сюда вызов функции сохранения в БД
            # await save_to_db(vacancies)
            
            print(f"Найдено {len(vacancies)} вакансий.")

if __name__ == "__main__":
    asyncio.run(main())