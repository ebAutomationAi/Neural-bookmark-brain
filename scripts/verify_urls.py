import asyncio
from sqlalchemy import select
from app.database import get_db_context
from app.models import Bookmark

async def test_view():
    async with get_db_context() as db:
        # Traemos 3 ejemplos que tengan URL limpia
        query = select(Bookmark.url, Bookmark.url_clean).where(Bookmark.url_clean.isnot(None)).limit(3)
        result = await db.execute(query)
        
        print("\n" + "🔍 MUESTRA DE LIMPIEZA DE URLS ".center(60, "="))
        for url, clean in result:
            print(f"🔹 ORIGINAL: {url}")
            print(f"✨ LIMPIA:   {clean}")
            print("-" * 60)

if __name__ == "__main__":
    asyncio.run(test_view())