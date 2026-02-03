from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from loguru import logger

from app.config import get_settings

settings = get_settings()

# Motor asíncrono
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=not settings.is_production,
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None,
    pool_size=10,
    max_overflow=20,
)

# Sesión asíncrona
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base declarativa
Base = declarative_base()


async def init_db():
    """Inicializa la base de datos y crea tablas"""
    try:
        async with engine.begin() as conn:
            # Habilitar extensión pgvector
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            logger.info("Extensión pgvector habilitada")
            
            # Crear todas las tablas
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Tablas creadas exitosamente")
            
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")
        raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency para obtener sesión de base de datos"""
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
    """Context manager para obtener sesión de base de datos"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db():
    """Cierra el engine de la base de datos"""
    await engine.dispose()
    logger.info("Conexión a base de datos cerrada")
