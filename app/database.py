from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from loguru import logger

from app.config import get_settings

try:
    settings = get_settings()
except Exception as e:
    print(f"Error cargando configuración: {e}")
    raise

Base = declarative_base()

if not settings.DATABASE_URL or not settings.DATABASE_URL.strip():
    raise ValueError(
        "DATABASE_URL no está configurada. Configúrala en .env (ej: cp .env.example .env)"
    )

try:
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False,
    )
except Exception as e:
    print(f"Error creando engine de base de datos: {e}")
    logger.error(f"Error creando engine de base de datos: {e}")
    raise

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def init_db():
    """Inicializa la base de datos"""
    try:
        async with engine.begin() as conn:
            # Crear extensión pgvector
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                logger.info("Extensión pgvector habilitada")
            except Exception as e:
                print(f"Error habilitando extensión pgvector: {e}")
                logger.error(f"Error habilitando extensión pgvector: {e}")
                raise
            
            # Crear tablas (sin checkfirst para forzar error si hay problema)
            try:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ Base de datos inicializada correctamente")
            except Exception as e:
                print(f"Error creando tablas: {e}")
                logger.error(f"Error creando tablas: {e}")
                raise
    except Exception as e:
        print("\n" + "="*60)
        print("❌ ERROR INICIALIZANDO BASE DE DATOS")
        print("="*60)
        print(f"Error: {e}")
        print("\nVerifica que:")
        print("1. PostgreSQL está corriendo")
        print("2. La base de datos existe")
        print("3. Las credenciales en DATABASE_URL son correctas")
        print("4. El usuario tiene permisos para crear extensiones")
        print("="*60 + "\n")
        raise

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