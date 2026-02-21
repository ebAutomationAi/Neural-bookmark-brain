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

# FIX: era ":" (anotación de tipo) en vez de "=" (asignación).
# TEST_DATABASE_URL: "postgresql+..." → variable siempre None → engine falla.
TEST_DATABASE_URL = (
    "postgresql+asyncpg://bookmark_user:bookmark_pass_2024"
    "@localhost:5432/neural_bookmarks_test"
)


@pytest.fixture(scope="session")
def event_loop():
    """Event loop para tests async - DEPRECATED: usar pytest_asyncio.fixture"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Session de DB limpia para cada test"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        # FIX: Usar Base.metadata.drop_all para limpiar TODO (tablas + índices)
        await conn.run_sync(Base.metadata.drop_all)
        
        # Dropear tablas manualmente como respaldo (por si acaso)
        await conn.execute(text("""
            DROP TABLE IF EXISTS bookmarks CASCADE;
            DROP TABLE IF EXISTS search_history CASCADE;
            DROP TABLE IF EXISTS processing_log CASCADE;
            DROP TABLE IF EXISTS alembic_version CASCADE;
        """))
        
        # FIX: Crear con checkfirst=True para evitar "already exists"
        def create_all_safe(conn):
            Base.metadata.create_all(conn, checkfirst=True)
        
        await conn.run_sync(create_all_safe)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    
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