#!/usr/bin/env python3
"""
Script para re-procesar bookmarks fallidos de forma resiliente
"""
import asyncio
import sys
import argparse
from pathlib import Path
from loguru import logger
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func, text
from sqlalchemy.orm.attributes import flag_modified
from app.database import get_db_context, init_db
from app.models import Bookmark
from app.agents import orchestrator


async def reprocess_failed_bookmarks(limit: int = None, batch_size: int = 5):
    """
    Re-procesa bookmarks con status 'failed' o 'pending'.
    Si se proporciona un limit, solo procesará esa cantidad.
    """
    logger.info("🔄 Iniciando re-procesamiento resiliente...")
    
    async with get_db_context() as db:
        # 1. Construcción de la consulta con límite real en SQL
        query = select(Bookmark).where(
            Bookmark.status.in_(['failed', 'pending'])
        ).order_by(Bookmark.created_at)
        
        if limit:
            query = query.limit(limit)
            logger.info(f"🔢 Límite de seguridad activado: {limit} registros")
        
        result = await db.execute(query)
        # Scalars().all() ahora solo traerá el número definido en limit
        bookmarks = result.scalars().all()
        
        total = len(bookmarks)
        
        if total == 0:
            logger.info("✅ No hay bookmarks pendientes para procesar")
            return

        logger.info(f"📊 {total} bookmarks cargados para esta sesión")
        
        processed = 0
        success_count = 0
        failed_count = 0
        
        # 2. Bucle por batches (segmentando la lista ya limitada)
        for i in range(0, total, batch_size):
            batch = bookmarks[i:i + batch_size]
            current_batch_num = i // batch_size + 1
            total_batches = (total - 1) // batch_size + 1
            
            logger.info(f"📦 Batch {current_batch_num}/{total_batches} (Tamaño: {len(batch)})")
            
            for bookmark in batch:
                try:
                    logger.info(f"  🔄 Procesando [{processed + 1}/{total}]: ID {bookmark.id} - {bookmark.url[:50]}...")
                    
                    # Estado intermedio para evitar colisiones
                    bookmark.status = "processing"
                    await db.commit()
                    
                    # Llamada al orquestador
                    res = await orchestrator.process_bookmark(
                        bookmark.url,
                        bookmark.original_title
                    )
                    
                    # Actualización de campos
                    bookmark.clean_title = res.get("clean_title") or bookmark.original_title
                    bookmark.summary = res.get("summary")
                    bookmark.full_text = res.get("full_text")
                    bookmark.tags = res.get("tags", []) or []
                    bookmark.category = res.get("category")
                    bookmark.is_nsfw = bool(res.get("is_nsfw", False))
                    bookmark.nsfw_reason = res.get("nsfw_reason")
                    bookmark.is_local = bool(res.get("is_local", False))
                    bookmark.domain = res.get("domain")
                    bookmark.language = res.get("language")
                    bookmark.word_count = int(res.get("word_count", 0))
                    bookmark.embedding = res.get("embedding")
                    bookmark.status = res.get("status", "failed")
                    bookmark.error_message = res.get("error")
                    bookmark.scraped_at = datetime.now()
                    
                    # Campos de limpieza de URL
                    bookmark.url_clean = res.get("url_clean") if res.get("url_clean") is not None else bookmark.url
                    bookmark.tracking_params = res.get("tracking_params")
                    
                    # Forzar detección de cambios en SQLAlchemy
                    flag_modified(bookmark, "url_clean")
                    flag_modified(bookmark, "tracking_params")
                    flag_modified(bookmark, "tags")
                    
                    await db.commit()
                    processed += 1
                    
                    if res.get("success"):
                        success_count += 1
                        logger.info(f"    ✅ ÉXITO ID {bookmark.id}: {bookmark.category}")
                    else:
                        failed_count += 1
                        logger.warning(f"    ❌ FALLO ID {bookmark.id}: {bookmark.error_message[:60]}")
                        
                        # Inserción en tabla de fallidos (SQL puro para velocidad)
                        try:
                            await db.execute(text('''
                                INSERT INTO failed_bookmarks 
                                (url_original, url_clean, domain, failure_reason, error_message, word_count, processing_time, bookmark_id)
                                VALUES (:url, :url_clean, :domain, :reason, :error, :words, :time, :bookmark_id)
                            '''), {
                                'url': bookmark.url,
                                'url_clean': res.get('url_clean'),
                                'domain': res.get('domain'),
                                'reason': 'timeout' if 'timeout' in str(res.get('error','')).lower() else 'http_error',
                                'error': res.get('error'),
                                'words': res.get('word_count', 0),
                                'time': res.get('processing_time', 0),
                                'bookmark_id': bookmark.id
                            })
                            await db.commit()
                        except Exception:
                            await db.rollback() # Evitar que un error aquí rompa el bucle
                
                except Exception as e:
                    logger.error(f"  ⚠️ Error crítico en bookmark {bookmark.id}: {str(e)}")
                    bookmark.status = "failed"
                    bookmark.error_message = str(e)
                    await db.commit()
                    failed_count += 1
                    continue

            # Pausa anti-bloqueo entre batches
            if i + batch_size < total:
                wait_time = 3
                logger.info(f"⏳ Esperando {wait_time}s para el siguiente batch...")
                await asyncio.sleep(wait_time)
        
        # Resumen final
        logger.info("=" * 60)
        logger.info(f"📊 RESUMEN: {success_count} exitosos, {failed_count} fallidos de {total} intentados")
        logger.info("=" * 60)


async def main():
    # 1. Configurar el lector de argumentos
    parser = argparse.ArgumentParser(description="Re-procesar marcadores fallidos")
    parser.add_argument('--limit', type=int, help='Cantidad máxima a procesar')
    
    # 2. Leer los argumentos de la terminal
    args = parser.parse_args()  # <--- AQUÍ ES DONDE SE DEFINE 'args'

    logger.info("🧠 Neural Bookmark Brain - Re-procesamiento Resiliente")
    logger.info("=" * 60)
    
    try:
        # 3. Pasar el límite a la función
        await reprocess_failed_bookmarks(limit=args.limit)
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())