from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from loguru import logger

from app.config import get_settings

settings = get_settings()
Base = declarative_base()

engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def init_db():
    """Inicializa la base de datos"""
    async with engine.begin() as conn:
        # Crear extensión pgvector
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        logger.info("Extensión pgvector habilitada")
        
        # Crear tablas (sin checkfirst para forzar error si hay problema)
        await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Base de datos inicializada correctamente")

async def close_db():
    await engine.dispose()
    logger.info("Conexión a base de datos cerrada")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@asynccontextmanager
async def get_db_context():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()