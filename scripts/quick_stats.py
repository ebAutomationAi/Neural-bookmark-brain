import asyncio
from sqlalchemy import select, func
from app.database import get_db_context
from app.models import Bookmark

async def get_summary():
    async with get_db_context() as db:
        # Ejecutamos las dos consultas que te interesan
        q_tracking = select(func.count()).where(Bookmark.tracking_params.isnot(None))
        q_clean = select(func.count()).where(Bookmark.url_clean.isnot(None))
        
        res_t = await db.execute(q_tracking)
        res_c = await db.execute(q_clean)
        
        print("\n" + "📊 REPORTE DE PROCESAMIENTO ".center(40, "="))
        print(f"🔍 Con tracking_params : {res_t.scalar()}")
        print(f"✨ Con url_clean       : {res_c.scalar()}")
        print("="*40 + "\n")

if __name__ == "__main__":
    asyncio.run(get_summary())