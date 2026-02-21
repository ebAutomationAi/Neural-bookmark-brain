# tests/integration/test_api.py
"""
Tests de integración para la API REST
"""
import pytest
from httpx import AsyncClient
from app.main import app
@pytest.mark.asyncio
async def test_health_endpoint():
    """Test del endpoint de health check"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "database" in data
        assert "version" in data
@pytest.mark.asyncio
async def test_root_endpoint():
    """Test del endpoint raíz"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Neural Bookmark Brain"
        assert "version" in data
@pytest.mark.asyncio
async def test_search_endpoint_basic(client, db_session):
    """Test básico del endpoint de búsqueda"""
    from app.models import Bookmark
    from app.services.embeddings import get_embedding_service
    
    embedding_service = get_embedding_service()
    
    bookmark = Bookmark(
        url="https://test.com",
        original_title="Test",
        clean_title="Python Tutorial",
        summary="Learn Python programming",
        tags=["python", "programming"],
        category="Programación",
        status="completed",
        embedding=embedding_service.generate_embedding("Python Tutorial. Learn Python programming")
    )
    db_session.add(bookmark)
    await db_session.commit()

    response = await client.post(
        "/search",
        json={"query": "python tutorial", "limit": 5}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["results"]) >= 1
    assert data["results"][0]["bookmark"]["clean_title"] == "Python Tutorial"
@pytest.mark.asyncio
async def test_search_with_filters(client, db_session):
    """Test de búsqueda con filtros de categoría y tags"""
    from app.models import Bookmark
    from app.services.embeddings import get_embedding_service
    
    embedding_service = get_embedding_service()
    
    # Crear múltiples bookmarks con diferentes categorías
    bookmarks = [
        Bookmark(
            url="https://test.com/python",
            original_title="Python Guide",
            clean_title="Python Guide",
            category="Programación",
            tags=["python"],
            status="completed",
            embedding=embedding_service.generate_embedding("Python")
        ),
        Bookmark(
            url="https://test.com/cooking",
            original_title="Cooking Recipe",
            clean_title="Cooking Recipe",
            category="Cocina",
            tags=["cooking"],
            status="completed",
            embedding=embedding_service.generate_embedding("Cooking")
        )
    ]
    
    for bookmark in bookmarks:
        db_session.add(bookmark)
    await db_session.commit()

    response = await client.post(
        "/search",
        json={
            "query": "guide",
            "category": "Programación",
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for result in data["results"]:
        assert result["bookmark"]["category"] == "Programación"
@pytest.mark.asyncio
async def test_search_nsfw_filter(client, db_session):
    """Test de filtrado de contenido NSFW en búsqueda"""
    from app.models import Bookmark
    from app.services.embeddings import get_embedding_service
    
    embedding_service = get_embedding_service()
    
    bookmarks = [
        Bookmark(
            url="https://test.com/safe",
            original_title="Safe Content",
            clean_title="Safe Content",
            is_nsfw=False,
            status="completed",
            embedding=embedding_service.generate_embedding("Safe")
        ),
        Bookmark(
            url="https://test.com/nsfw",
            original_title="NSFW Content",
            clean_title="NSFW Content",
            is_nsfw=True,
            status="completed",
            embedding=embedding_service.generate_embedding("NSFW")
        )
    ]
    
    for bookmark in bookmarks:
        db_session.add(bookmark)
    await db_session.commit()

    response = await client.post(
        "/search",
        json={"query": "content", "include_nsfw": False}
    )
    assert response.status_code == 200
    data = response.json()
    for result in data["results"]:
        assert result["bookmark"]["is_nsfw"] is False
@pytest.mark.asyncio
async def test_stats_processing_endpoint():
    """Test del endpoint de estadísticas de procesamiento"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/stats/processing")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "completed" in data
        assert "pending" in data
        assert "failed" in data
@pytest.mark.asyncio
async def test_stats_categories_endpoint(client, db_session):
    """Test del endpoint de estadísticas de categorías"""
    from app.models import Bookmark
    
    # Crear bookmarks con categorías
    bookmarks = [
        Bookmark(url=f"https://test.com/{i}", original_title=f"Test {i}", category="Testing", status="completed")
        for i in range(3)
    ]
    for bookmark in bookmarks:
        db_session.add(bookmark)
    await db_session.commit()

    response = await client.get("/stats/categories")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert isinstance(data["categories"], list)
@pytest.mark.asyncio
async def test_get_bookmark_by_id(client, db_session):
    """Test de obtener bookmark por ID"""
    from app.models import Bookmark
    
    bookmark = Bookmark(
        url="https://test.com/specific",
        original_title="Specific Test",
        status="completed"
    )
    db_session.add(bookmark)
    await db_session.commit()
    await db_session.refresh(bookmark)

    response = await client.get(f"/bookmarks/{bookmark.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == bookmark.id
    assert data["url"] == "https://test.com/specific"
@pytest.mark.asyncio
async def test_get_bookmark_not_found(client):
    """Test de bookmark no encontrado"""

    response = await client.get("/bookmarks/99999")
    assert response.status_code == 404
@pytest.mark.asyncio
async def test_list_bookmarks(client, db_session):
    """Test de listar bookmarks con paginación"""
    from app.models import Bookmark
    
    # Crear múltiples bookmarks
    for i in range(5):
        bookmark = Bookmark(
            url=f"https://test.com/bookmark-{i}",
            original_title=f"Bookmark {i}",
            status="completed"
        )
        db_session.add(bookmark)
    await db_session.commit()

    response = await client.get("/bookmarks?skip=0&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 3
@pytest.mark.asyncio
async def test_search_empty_query():
    """Test de búsqueda con query vacía"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/search",
            json={"query": "", "limit": 5}
        )
        assert response.status_code in [200, 400, 422]
@pytest.mark.asyncio
async def test_search_similarity_scores(client, db_session):
    """Test de que los scores de similitud están en el rango correcto"""
    from app.models import Bookmark
    from app.services.embeddings import get_embedding_service
    
    embedding_service = get_embedding_service()
    
    bookmark = Bookmark(
        url="https://test.com/similarity",
        original_title="Machine Learning Tutorial",
        clean_title="Machine Learning Tutorial",
        status="completed",
        embedding=embedding_service.generate_embedding("Machine Learning Tutorial")
    )
    db_session.add(bookmark)
    await db_session.commit()

    response = await client.post(
        "/search",
        json={"query": "machine learning", "limit": 5}
    )
    assert response.status_code == 200
    data = response.json()
    for result in data["results"]:
        score = result["similarity_score"]
        assert 0.0 <= score <= 1.0
if __name__ == "__main__":
    pytest.main([__file__, "-v"])