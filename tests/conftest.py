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
    """Session de DB limpia para cada test"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        # FIX: Dropear TODO en orden correcto - primero índices, luego tablas
        # Usar CASCADE para forzar eliminación de dependencias
        
        # 1. Dropear índices manualmente primero (evita errores de "already exists")
        await conn.execute(text("""
            DO $$ 
            BEGIN
                -- Dropear todos los índices de bookmarks si existen
                IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_bookmarks_domain') THEN
                    EXECUTE 'DROP INDEX IF EXISTS ix_bookmarks_domain CASCADE';
                END IF;
                
                IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_bookmarks_status') THEN
                    EXECUTE 'DROP INDEX IF EXISTS ix_bookmarks_status CASCADE';
                END IF;
                
                IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_bookmarks_category') THEN
                    EXECUTE 'DROP INDEX IF EXISTS ix_bookmarks_category CASCADE';
                END IF;
                
                IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_bookmarks_nsfw') THEN
                    EXECUTE 'DROP INDEX IF EXISTS ix_bookmarks_nsfw CASCADE';
                END IF;
                
                IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_bookmarks_created_at') THEN
                    EXECUTE 'DROP INDEX IF EXISTS ix_bookmarks_created_at CASCADE';
                END IF;
            END $$;
        """))
        
        # 2. Dropear tablas en orden correcto (dependencias primero)
        await conn.execute(text("DROP TABLE IF EXISTS processing_log CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS search_history CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS bookmarks CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        
        # 3. Limpiar cualquier tabla residual que pueda quedar
        await conn.execute(text("""
            DO $$
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """))
        
        # 4. Crear extensión vector primero
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        
        # 5. Crear todo el schema fresco
        def create_all_safe(conn):
            # Sin checkfirst - queremos crear todo de cero
            Base.metadata.create_all(conn)
        
        await conn.run_sync(create_all_safe)
    
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