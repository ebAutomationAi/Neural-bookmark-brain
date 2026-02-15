from app.database import get_db_context
import asyncio
from app.models import Bookmark
from sqlalchemy import select, func

async def tracking_stats():
    async with get_db_context() as db:
        # 1. Contar total con tracking
        result = await db.execute(
            select(Bookmark.tracking_params).where(
                Bookmark.status == 'completed',
                Bookmark.tracking_params.isnot(None)
            )
        )
        all_tracking = result.scalars().all()
        
        print('\n=== ANÁLISIS DE PRIVACIDAD Y TRACKING ===')
        print(f'Total marcadores analizados : {len(all_tracking)}')
        
        if all_tracking:
            print('\nEjemplos de parámetros detectados y eliminados:')
            for i, params in enumerate(all_tracking[:5], 1):
                if params:
                    keys = list(params.keys())
                    print(f'  [{i}] {", ".join(keys[:4])}{"..." if len(keys) > 4 else ""}')
        
        # 2. Top dominios con más basura de tracking
        result = await db.execute(
            select(Bookmark.domain, func.count()).where(
                Bookmark.status == 'completed',
                Bookmark.tracking_params.isnot(None)
            ).group_by(Bookmark.domain).order_by(func.count().desc()).limit(10)
        )
        top_domains = result.fetchall()
        
        if top_domains:
            print('\nTop dominios con mayor carga de tracking:')
            print(f'  {"Dominio":30} | {"Casos":5}')
            print(f'  {"-"*30}-|-------')
            for domain, count in top_domains:
                print(f'  {domain:30} | {count:5}')

if __name__ == "__main__":
    asyncio.run(tracking_stats())