import asyncio
from parsers.hh_parser import HHParser
from db.save import save_vacancies
from db.connection import close_db_pool

async def main():
    print("Запуск парсинга HH.kz...")
    parser = HHParser()
    
    # Ключевые слова для наполнения базы
    keywords = ["Python", "Разработчик", "Data Analyst", "Официант", "Менеджер"]
    
    for kw in keywords:
        print(f"Парсим вакансии по запросу: {kw}")
        vacancies = await parser.parse(query=kw, limit=30)
        if vacancies:
            await save_vacancies("hh.kz", vacancies)
            print(f"Сохранено {len(vacancies)} вакансий.")
        else:
            print(f"По запросу '{kw}' ничего не найдено или произошла ошибка.")
            
    await close_db_pool()
    print("Парсинг успешно завершен!")

if __name__ == "__main__":
    asyncio.run(main())