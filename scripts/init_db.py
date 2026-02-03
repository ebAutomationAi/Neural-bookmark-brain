#!/usr/bin/env python3
"""
Script para inicializar la base de datos
"""
import asyncio
import sys
from pathlib import Path

# Añadir directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from app.database import init_db, engine
from app.config import get_settings

settings = get_settings()


async def main():
    """Inicializa la base de datos"""
    logger.info("🔧 Inicializando base de datos...")
    
    try:
        # Inicializar DB
        await init_db()
        
        logger.info("✅ Base de datos inicializada correctamente")
        logger.info(f"   Database: {settings.DATABASE_URL.split('@')[1]}")
        
        # Cerrar conexión
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
