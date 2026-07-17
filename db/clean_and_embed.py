import re
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from db.connection import get_db_pool

# Загружаем модель
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator=" ")
    text = re.sub(r'\s+', ' ', text).strip()
    return text

async def process_embeddings():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Теперь колонка существует и мы можем фильтровать пустые
        records = await conn.fetch(
            "SELECT id, title, description_raw FROM vacancies WHERE embedding IS NULL"
        )
        
        if not records:
            print("Нет новых вакансий для генерации эмбеддингов.")
            return

        print(f"Генерируем эмбеддинги для {len(records)} вакансий...")
        
        for r in records:
            clean_text = clean_html(r['description_raw'])
            full_text_to_embed = f"{r['title']}. {clean_text}"
            
            # Получаем вектор и преобразуем его в список float
            embedding = [float(x) for x in model.encode(full_text_to_embed)]
            
            await conn.execute(
                "UPDATE vacancies SET description_clean = $1, embedding = $2 WHERE id = $3",
                clean_text, embedding, r['id']
            )
            print(f" ✓ Вектор сгенерирован для: {r['title']}")