# tests/conftest.py
import pytest
import pytest_asyncio
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport
from app.database import Base, get_db
from app.main import app
from app.config import get_settings

settings = get_settings()

TEST_DATABASE_URL = (
    "postgresql+asyncpg://bookmark_user:bookmark_pass_2024"
    "@localhost:5432/neural_bookmarks_test"
)


@pytest.fixture(scope="session")
def event_loop():
    """Event loop para tests async"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """
    Proporciona una sesión de base de datos limpia para cada test.
    El esquema se recrea completamente antes de la sesión del test.
    """
    # --- 1. Resetear completamente la base de datos en una transacción separada ---
    clean_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with clean_engine.begin() as conn:
        # Eliminar todo el esquema público y recrearlo
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        # Re-habilitar la extensión pgvector (necesaria para los campos Vector)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Crear todas las tablas desde cero
        await conn.run_sync(Base.metadata.create_all)
    # La transacción se confirma automáticamente al salir del bloque
    await clean_engine.dispose()

    # --- 2. Crear el motor y la sesión que usará el test ---
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    """Cliente HTTP que usa la base de datos de test."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_bookmark_data():
    """Datos de prueba reutilizables"""
    return {
        "url": "https://example.com/test",
        "title": "Test Article",
        "text": "This is a sample text about machine learning and Python.",
    }