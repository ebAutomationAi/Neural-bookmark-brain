# tests/conftest.py
import pytest
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient
from app.database import Base, get_db
from app.main import app
from app.config import get_settings

settings = get_settings()

# Base de datos de prueba (crear con: createdb neural_bookmarks_test && psql -d neural_bookmarks_test -c "CREATE EXTENSION vector;")
TEST_DATABASE_URL = "postgresql+asyncpg://bookmark_user:bookmark_pass_2024@localhost:5432/neural_bookmarks_test"

@pytest.fixture(scope="session")
def event_loop():
    """Event loop para tests async"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session():
    """Session de DB limpia para cada test"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()

@pytest.fixture
async def client(db_session):
    """Cliente HTTP que usa la base de datos de test (db_session)."""
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def sample_bookmark_data():
    """Datos de prueba reutilizables"""
    return {
        "url": "https://example.com/test",
        "title": "Test Article",
        "text": "This is a sample text about machine learning and Python.",
    }