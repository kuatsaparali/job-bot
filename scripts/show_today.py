from database.db_manager import get_todays_vacancies

def show_results():
    vacancies = get_todays_vacancies()
    
    if not vacancies:
        print("На сегодня новых вакансий пока нет.")
        return

    print(f"--- Свежие вакансии за сегодня ({len(vacancies)} шт.) ---")
    for title, url in vacancies:
        print(f"• {title}\n  {url}\n")

if __name__ == "__main__":
    show_results()