import asyncio
from db.clean_and_embed import process_embeddings
from db.connection import close_db_pool

async def main():
    print("Старт обработки текстов и генерации векторов...")
    await process_embeddings()
    await close_db_pool()
    print("ИИ-обработка векторов завершена!")

if __name__ == "__main__":
    asyncio.run(main())