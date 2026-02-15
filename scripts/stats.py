import asyncio
from sqlalchemy import select, func
from app.database import get_db_context
from app.models import Bookmark

async def get_stats():
    async with get_db_context() as db:
        # Consulta 1: Con tracking_params
        q1 = select(func.count()).where(Bookmark.tracking_params.isnot(None))
        res1 = await db.execute(q1)
        tracking_count = res1.scalar()

        # Consulta 2: Con url_clean
        q2 = select(func.count()).where(Bookmark.url_clean.isnot(None))
        res2 = await db.execute(q2)
        clean_count = res2.scalar()

        # Consulta 3: Total procesados
        q3 = select(func.count()).where(Bookmark.status == 'completed')
        res3 = await db.execute(q3)
        completed_count = res3.scalar()

        print("\n" + "📊 ESTADO DE LA BASE DE DATOS ".center(40, "="))
        print(f"✅ Total completados:      {completed_count}")
        print(f"✅ Con URL limpia:         {clean_count}")
        print(f"✅ Con parámetros detectados: {tracking_count}")
        print("="*40 + "\n")

if __name__ == "__main__":
    asyncio.run(get_stats())