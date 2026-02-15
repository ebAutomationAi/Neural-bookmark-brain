import asyncio
from sqlalchemy import select, func
from app.database import get_db_context
from app.models import Bookmark

async def check_stats():
    async with get_db_context() as db:
        # Contamos cuántos han completado la limpieza de URL
        query = (
            select(func.count())
            .where(Bookmark.status == 'completed')
            .where(Bookmark.url_clean.isnot(None))
        )
        result = await db.execute(query)
        count = result.scalar()
        
        print(f"\n" + "="*40)
        print(f"✅ Marcadores con url_clean: {count}")
        print("="*40 + "\n")

if __name__ == "__main__":
    asyncio.run(check_stats())