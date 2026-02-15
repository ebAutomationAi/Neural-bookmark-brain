# tests/integration/test_database.py
"""
Tests de integración para la base de datos
"""
import pytest
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Bookmark, SearchHistory, ProcessingLog
from app.services.embeddings import get_embedding_service


@pytest.mark.asyncio
async def test_database_connection(db_session: AsyncSession):
    """Test básico de conexión a la base de datos"""
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_pgvector_extension(db_session: AsyncSession):
    """Verifica que la extensión pgvector está instalada"""
    result = await db_session.execute(
        text("SELECT * FROM pg_extension WHERE extname = 'vector'")
    )
    extension = result.first()
    assert extension is not None, "Extensión pgvector no está instalada"


@pytest.mark.asyncio
async def test_create_bookmark(db_session: AsyncSession):
    """Test de creación de bookmark en la BD"""
    embedding_service = get_embedding_service()
    
    bookmark = Bookmark(
        url="https://test.com/article",
        original_title="Test Article",
        clean_title="Clean Test Article",
        summary="This is a test article about testing",
        full_text="Full text content here",
        tags=["test", "article"],
        category="Testing",
        status="completed",
        embedding=embedding_service.generate_embedding("Test content"),
        domain="test.com",
        language="en",
        word_count=10,
        is_nsfw=False
    )
    
    db_session.add(bookmark)
    await db_session.commit()
    await db_session.refresh(bookmark)
    
    assert bookmark.id is not None
    assert bookmark.url == "https://test.com/article"
    assert bookmark.status == "completed"
    assert bookmark.embedding is not None
    assert len(bookmark.tags) == 2


@pytest.mark.asyncio
async def test_query_bookmarks(db_session: AsyncSession):
    """Test de consulta de bookmarks"""
    embedding_service = get_embedding_service()
    
    # Crear varios bookmarks
    bookmarks = [
        Bookmark(
            url=f"https://test.com/{i}",
            original_title=f"Article {i}",
            clean_title=f"Clean Article {i}",
            status="completed",
            embedding=embedding_service.generate_embedding(f"Article {i}")
        )
        for i in range(3)
    ]
    
    for bookmark in bookmarks:
        db_session.add(bookmark)
    
    await db_session.commit()
    
    # Consultar todos
    result = await db_session.execute(select(Bookmark))
    all_bookmarks = result.scalars().all()
    
    assert len(all_bookmarks) == 3


@pytest.mark.asyncio
async def test_search_history(db_session: AsyncSession):
    """Test de historial de búsquedas"""
    search = SearchHistory(
        query="test query",
        results_count=5
    )
    
    db_session.add(search)
    await db_session.commit()
    await db_session.refresh(search)
    
    assert search.id is not None
    assert search.query == "test query"
    assert search.results_count == 5
    assert search.created_at is not None


@pytest.mark.asyncio
async def test_processing_log(db_session: AsyncSession):
    """Test de log de procesamiento"""
    # Crear bookmark primero
    bookmark = Bookmark(
        url="https://test.com/log-test",
        original_title="Log Test",
        status="pending"
    )
    db_session.add(bookmark)
    await db_session.commit()
    await db_session.refresh(bookmark)
    
    # Crear log
    log = ProcessingLog(
        bookmark_id=bookmark.id,
        url=bookmark.url,
        agent_name="test_agent",
        success=True,
        processing_time=1.5
    )
    
    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)
    
    assert log.id is not None
    assert log.bookmark_id == bookmark.id
    assert log.success is True
    assert log.processing_time == 1.5


@pytest.mark.asyncio
async def test_vector_similarity_search(db_session: AsyncSession):
    """Test de búsqueda por similitud vectorial"""
    embedding_service = get_embedding_service()
    
    # Crear bookmarks con embeddings
    bookmarks_data = [
        ("Python programming tutorial", ["python", "programming"]),
        ("JavaScript web development", ["javascript", "web"]),
        ("Machine learning basics", ["ml", "ai"]),
    ]
    
    for text, tags in bookmarks_data:
        bookmark = Bookmark(
            url=f"https://test.com/{text.replace(' ', '-')}",
            original_title=text,
            clean_title=text,
            tags=tags,
            status="completed",
            embedding=embedding_service.generate_embedding(text)
        )
        db_session.add(bookmark)
    
    await db_session.commit()
    
    # Buscar similar a "Python programming"
    query_embedding = embedding_service.generate_embedding("Python programming")
    
    result = await db_session.execute(
        select(Bookmark)
        .where(Bookmark.status == "completed")
        .order_by(Bookmark.embedding.cosine_distance(query_embedding))
        .limit(3)
    )
    
    results = result.scalars().all()
    
    assert len(results) > 0
    # El primer resultado debería ser el más similar (Python)
    assert "python" in results[0].clean_title.lower()


@pytest.mark.asyncio
async def test_bookmark_status_workflow(db_session: AsyncSession):
    """Test del flujo de estados de un bookmark"""
    bookmark = Bookmark(
        url="https://test.com/workflow",
        original_title="Workflow Test",
        status="pending"
    )
    
    db_session.add(bookmark)
    await db_session.commit()
    await db_session.refresh(bookmark)
    
    # Verificar estado inicial
    assert bookmark.status == "pending"
    
    # Cambiar a processing
    bookmark.status = "processing"
    await db_session.commit()
    await db_session.refresh(bookmark)
    assert bookmark.status == "processing"
    
    # Cambiar a completed
    bookmark.status = "completed"
    bookmark.clean_title = "Completed Workflow Test"
    await db_session.commit()
    await db_session.refresh(bookmark)
    assert bookmark.status == "completed"


@pytest.mark.asyncio
async def test_nsfw_filter(db_session: AsyncSession):
    """Test de filtrado de contenido NSFW"""
    embedding_service = get_embedding_service()
    
    # Crear bookmarks normales y NSFW
    bookmark_safe = Bookmark(
        url="https://test.com/safe",
        original_title="Safe Content",
        status="completed",
        is_nsfw=False,
        embedding=embedding_service.generate_embedding("Safe")
    )
    
    bookmark_nsfw = Bookmark(
        url="https://test.com/nsfw",
        original_title="NSFW Content",
        status="completed",
        is_nsfw=True,
        nsfw_reason="Contains adult content",
        embedding=embedding_service.generate_embedding("NSFW")
    )
    
    db_session.add(bookmark_safe)
    db_session.add(bookmark_nsfw)
    await db_session.commit()
    
    # Consultar solo contenido seguro
    result = await db_session.execute(
        select(Bookmark).where(Bookmark.is_nsfw == False)
    )
    safe_bookmarks = result.scalars().all()
    
    assert len(safe_bookmarks) == 1
    assert safe_bookmarks[0].url == "https://test.com/safe"


@pytest.mark.asyncio
async def test_bookmark_tags_array(db_session: AsyncSession):
    """Test de manejo de tags como array PostgreSQL"""
    bookmark = Bookmark(
        url="https://test.com/tags",
        original_title="Tags Test",
        tags=["python", "testing", "database"],
        status="completed"
    )
    
    db_session.add(bookmark)
    await db_session.commit()
    await db_session.refresh(bookmark)
    
    assert len(bookmark.tags) == 3
    assert "python" in bookmark.tags
    assert "testing" in bookmark.tags
    
    # Verificar que se puede buscar por tags
    result = await db_session.execute(
        select(Bookmark).where(Bookmark.tags.contains(["python"]))
    )
    found = result.scalar_one_or_none()
    assert found is not None
    assert found.url == "https://test.com/tags"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
