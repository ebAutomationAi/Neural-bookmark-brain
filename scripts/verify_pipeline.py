from app.database import get_db_context
import asyncio
from app.models import Bookmark
from sqlalchemy import select, func
import numpy as np

async def verify():
    async with get_db_context() as db:
        # 1. Obtener total completados
        total_res = await db.execute(select(func.count()).where(Bookmark.status == 'completed'))
        completed = total_res.scalar() or 0

        # 2. Obtener 5 ejemplos
        result = await db.execute(
            select(Bookmark).where(Bookmark.status == 'completed').limit(5)
        )
        bookmarks = result.scalars().all()
        
        print(f'\n=== VERIFICACIÓN DE CAMPOS CRÍTICOS ({len(bookmarks)} ejemplos) ===')
        for i, bm in enumerate(bookmarks, 1):
            # Verificación segura de embedding
            emb_status = "❌ NULL"
            if bm.embedding is not None:
                emb_len = len(bm.embedding)
                emb_status = "✅" if emb_len == 384 else f"❌ {emb_len}d"

            print(f'\n[{i}] {bm.url[:60]}...')
            print(f'    url_clean       : {"✅" if bm.url_clean else "❌ NULL"}')
            print(f'    clean_title     : {"✅" if bm.clean_title and len(bm.clean_title) > 5 else "❌ Vacío/corto"}')
            print(f'    summary         : {"✅" if bm.summary and len(bm.summary) > 20 else "❌ Vacío/corto"}')
            print(f'    embedding       : {emb_status}')
            print(f'    category        : {bm.category or "N/A"}')
        
        # 3. Estadísticas agregadas
        print('\n=== ESTADÍSTICAS AGREGADAS ===')
        if completed > 0:
            # Simplificamos la query para evitar problemas de tipos en el conteo
            print(f'Total completados   : {completed}')
            
            # Contar embeddings reales
            emb_res = await db.execute(select(func.count()).where(Bookmark.status == 'completed', Bookmark.embedding.isnot(None)))
            emb_ok = emb_res.scalar() or 0
            
            # Contar categorías
            cat_res = await db.execute(select(func.count()).where(Bookmark.status == 'completed', Bookmark.category.isnot(None)))
            cat_ok = cat_res.scalar() or 0

            print(f'Embeddings (384d)   : {emb_ok} / {completed}')
            print(f'Categorías asignadas: {cat_ok} / {completed}')
        else:
            print("No hay marcadores con status 'completed' todavía.")

if __name__ == "__main__":
    asyncio.run(verify())