#!/usr/bin/env python3
"""
Script para importar bookmarks desde CSV
"""
import asyncio
import sys
from pathlib import Path
import pandas as pd
from loguru import logger
from datetime import datetime
from typing import List, Dict

# Añadir directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import get_db_context, init_db
from app.models import Bookmark, ProcessingLog
from app.schemas import ImportStats
from app.agents import orchestrator
from app.utils.validators import URLValidator
from app.config import get_settings

settings = get_settings()


class BookmarkImporter:
    """Importador de bookmarks desde CSV"""
    
    def __init__(self, csv_path: str, batch_size: int = 10):
        self.csv_path = Path(csv_path)
        self.batch_size = batch_size
        self.stats = {
            "total_bookmarks": 0,
            "imported": 0,
            "duplicates": 0,
            "failed": 0,
            "nsfw_detected": 0,
            "local_detected": 0,
            "errors": []
        }
    
    async def import_bookmarks(self):
        """Importa bookmarks desde CSV"""
        logger.info(f"📥 Importando bookmarks desde: {self.csv_path}")
        
        # Verificar que el archivo existe
        if not self.csv_path.exists():
            logger.error(f"❌ Archivo no encontrado: {self.csv_path}")
            return self.stats
        
        try:
            # Leer CSV
            df = pd.read_csv(self.csv_path)
            logger.info(f"📊 CSV cargado: {len(df)} filas")
            
            # Validar columnas
            if 'url' not in df.columns or 'title' not in df.columns:
                logger.error("❌ CSV debe contener columnas 'url' y 'title'")
                return self.stats
            
            # Limpiar datos
            df = df.dropna(subset=['url'])  # Eliminar URLs vacías
            df['title'] = df['title'].fillna('Sin título')  # Rellenar títulos vacíos
            
            self.stats["total_bookmarks"] = len(df)
            
            logger.info(f"🚀 Procesando {len(df)} bookmarks...")
            
            # Procesar en batches
            for i in range(0, len(df), self.batch_size):
                batch = df.iloc[i:i + self.batch_size]
                logger.info(f"📦 Batch {i // self.batch_size + 1}/{(len(df) - 1) // self.batch_size + 1}")
                
                await self._process_batch(batch)
                
                # Pausa entre batches para no saturar
                await asyncio.sleep(1)
            
            # Resumen final
            logger.info("=" * 60)
            logger.info("📊 RESUMEN DE IMPORTACIÓN")
            logger.info("=" * 60)
            logger.info(f"Total procesados:  {self.stats['total_bookmarks']}")
            logger.info(f"✅ Importados:     {self.stats['imported']}")
            logger.info(f"🔄 Duplicados:     {self.stats['duplicates']}")
            logger.info(f"❌ Fallidos:       {self.stats['failed']}")
            logger.info(f"🔞 NSFW:           {self.stats['nsfw_detected']}")
            logger.info(f"🏠 Locales:        {self.stats['local_detected']}")
            logger.info("=" * 60)
            
            if self.stats["errors"]:
                logger.warning(f"⚠️  {len(self.stats['errors'])} errores registrados")
            
            return self.stats
        
        except Exception as e:
            logger.error(f"❌ Error importando CSV: {e}")
            self.stats["errors"].append(str(e))
            return self.stats
    
    async def _process_batch(self, batch: pd.DataFrame):
        """Procesa un batch de bookmarks"""
        async with get_db_context() as db:
            for _, row in batch.iterrows():
                url = row['url']
                title = row['title']
                
                try:
                    # Validar y normalizar URL
                    is_valid, normalized_url, error = URLValidator.validate_and_normalize(url)
                    
                    if not is_valid:
                        logger.warning(f"⚠️  URL inválida: {url} ({error})")
                        self.stats["failed"] += 1
                        self.stats["errors"].append(f"URL inválida: {url}")
                        continue
                    
                    # Verificar duplicados
                    result = await db.execute(
                        select(Bookmark).where(Bookmark.url == normalized_url)
                    )
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        logger.info(f"🔄 Duplicado: {normalized_url}")
                        self.stats["duplicates"] += 1
                        continue
                    
                    # Crear bookmark inicial
                    bookmark = Bookmark(
                        url=normalized_url,
                        original_title=title,
                        status="pending"
                    )
                    
                    db.add(bookmark)
                    await db.commit()
                    await db.refresh(bookmark)
                    
                    logger.info(f"✅ Bookmark creado: {bookmark.id} - {normalized_url}")
                    
                    # Procesar con agentes
                    await self._process_bookmark(db, bookmark)
                
                except Exception as e:
                    logger.error(f"❌ Error procesando {url}: {e}")
                    self.stats["failed"] += 1
                    self.stats["errors"].append(f"{url}: {str(e)}")
    
    async def _process_bookmark(self, db, bookmark: Bookmark):
        """Procesa un bookmark con los agentes"""
        try:
            # Marcar como procesando
            bookmark.status = "processing"
            await db.commit()
            
            # Procesar con orquestador
            result = await orchestrator.process_bookmark(
                bookmark.url,
                bookmark.original_title
            )
            
            # Actualizar bookmark con resultados
            bookmark.clean_title = result.get("clean_title")
            bookmark.summary = result.get("summary")
            bookmark.full_text = result.get("full_text")
            bookmark.tags = result.get("tags", [])
            bookmark.category = result.get("category")
            bookmark.is_nsfw = result.get("is_nsfw", False)
            bookmark.nsfw_reason = result.get("nsfw_reason")
            bookmark.is_local = result.get("is_local", False)
            bookmark.domain = result.get("domain")
            bookmark.language = result.get("language")
            bookmark.word_count = result.get("word_count", 0)
            bookmark.embedding = result.get("embedding")
            bookmark.status = result.get("status", "failed")
            bookmark.error_message = result.get("error")
            bookmark.scraped_at = datetime.now()
            
            await db.commit()
            
            # Actualizar estadísticas
            if result.get("success"):
                self.stats["imported"] += 1
                
                if bookmark.is_nsfw:
                    self.stats["nsfw_detected"] += 1
                
                if bookmark.is_local:
                    self.stats["local_detected"] += 1
                
                logger.info(
                    f"✅ Procesado: {bookmark.id} - {bookmark.clean_title} "
                    f"(Status: {bookmark.status})"
                )
            else:
                self.stats["failed"] += 1
                logger.error(
                    f"❌ Fallo: {bookmark.id} - {bookmark.url} "
                    f"(Error: {bookmark.error_message})"
                )
            
            # Log de procesamiento
            log = ProcessingLog(
                bookmark_id=bookmark.id,
                url=bookmark.url,
                agent_name="orchestrator",
                success=result.get("success", False),
                error_message=result.get("error"),
                processing_time=result.get("processing_time", 0)
            )
            db.add(log)
            await db.commit()
        
        except Exception as e:
            logger.error(f"❌ Error procesando bookmark {bookmark.id}: {e}")
            bookmark.status = "failed"
            bookmark.error_message = str(e)
            await db.commit()
            
            self.stats["failed"] += 1
            self.stats["errors"].append(f"{bookmark.url}: {str(e)}")


async def main():
    """Función principal"""
    # Argumentos
    if len(sys.argv) < 2:
        logger.error("❌ Uso: python import_csv.py <archivo.csv> [batch_size]")
        logger.info("Ejemplo: python import_csv.py data/bookmarks.csv 10")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    logger.info("🧠 Neural Bookmark Brain - Importador CSV")
    logger.info("=" * 60)
    
    try:
        # Inicializar DB
        logger.info("🔧 Inicializando base de datos...")
        await init_db()
        logger.info("✅ Base de datos lista")
        
        # Importar bookmarks
        importer = BookmarkImporter(csv_path, batch_size)
        stats = await importer.import_bookmarks()
        
        logger.info("🎉 Importación completada!")
        
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
