#!/usr/bin/env python3
"""
Script de ejemplo para interactuar con la Neural Bookmark Brain API
"""
import requests
import json
from typing import List, Dict


class NeuralBookmarkClient:
    """Cliente de ejemplo para la API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def health_check(self) -> Dict:
        """Verifica el estado del sistema"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def search(
        self,
        query: str,
        limit: int = 10,
        include_nsfw: bool = False,
        category: str = None
    ) -> Dict:
        """Búsqueda semántica"""
        payload = {
            "query": query,
            "limit": limit,
            "include_nsfw": include_nsfw
        }
        
        if category:
            payload["category"] = category
        
        response = requests.post(
            f"{self.base_url}/search",
            json=payload
        )
        
        return response.json()
    
    def get_bookmarks(
        self,
        skip: int = 0,
        limit: int = 50,
        status_filter: str = None,
        category: str = None
    ) -> List[Dict]:
        """Lista bookmarks"""
        params = {
            "skip": skip,
            "limit": limit
        }
        
        if status_filter:
            params["status_filter"] = status_filter
        
        if category:
            params["category"] = category
        
        response = requests.get(
            f"{self.base_url}/bookmarks",
            params=params
        )
        
        return response.json()
    
    def get_bookmark(self, bookmark_id: int) -> Dict:
        """Obtiene un bookmark específico"""
        response = requests.get(f"{self.base_url}/bookmarks/{bookmark_id}")
        return response.json()
    
    def reprocess_bookmark(self, bookmark_id: int) -> Dict:
        """Re-procesa un bookmark"""
        response = requests.post(f"{self.base_url}/process/{bookmark_id}")
        return response.json()
    
    def get_processing_stats(self) -> Dict:
        """Obtiene estadísticas de procesamiento"""
        response = requests.get(f"{self.base_url}/stats/processing")
        return response.json()
    
    def get_category_stats(self) -> Dict:
        """Estadísticas por categoría"""
        response = requests.get(f"{self.base_url}/stats/categories")
        return response.json()
    
    def get_tag_stats(self, limit: int = 20) -> Dict:
        """Top tags"""
        response = requests.get(
            f"{self.base_url}/stats/tags",
            params={"limit": limit}
        )
        return response.json()


def main():
    """Ejemplos de uso"""
    client = NeuralBookmarkClient()
    
    print("=" * 60)
    print("🧠 Neural Bookmark Brain - Cliente de Ejemplo")
    print("=" * 60)
    
    # 1. Health Check
    print("\n1️⃣  Health Check...")
    health = client.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Database: {health['database']}")
    
    # 2. Estadísticas de procesamiento
    print("\n2️⃣  Estadísticas de Procesamiento...")
    stats = client.get_processing_stats()
    print(f"   Total: {stats['total']}")
    print(f"   Completados: {stats['completed']}")
    print(f"   Pendientes: {stats['pending']}")
    print(f"   Fallidos: {stats['failed']}")
    
    # 3. Top Categorías
    print("\n3️⃣  Top Categorías...")
    categories = client.get_category_stats()
    for cat in categories['categories'][:5]:
        print(f"   - {cat['category']}: {cat['count']}")
    
    # 4. Top Tags
    print("\n4️⃣  Top Tags...")
    tags = client.get_tag_stats(limit=10)
    for tag in tags['tags'][:10]:
        print(f"   - #{tag['tag']}: {tag['count']}")
    
    # 5. Búsqueda semántica
    print("\n5️⃣  Búsqueda Semántica: 'machine learning tutorials'...")
    results = client.search("machine learning tutorials", limit=3)
    
    print(f"   Query: {results['query']}")
    print(f"   Resultados: {results['total']}")
    print(f"   Tiempo: {results['execution_time']:.3f}s")
    print("\n   Top 3 Resultados:")
    
    for i, result in enumerate(results['results'][:3], 1):
        bookmark = result['bookmark']
        score = result['similarity_score']
        print(f"\n   {i}. {bookmark['clean_title']}")
        print(f"      URL: {bookmark['url'][:60]}...")
        print(f"      Categoría: {bookmark.get('category', 'N/A')}")
        print(f"      Tags: {', '.join(bookmark.get('tags', [])[:3])}")
        print(f"      Score: {score:.3f}")
    
    # 6. Listar bookmarks recientes
    print("\n6️⃣  Últimos 5 Bookmarks Completados...")
    bookmarks = client.get_bookmarks(
        limit=5,
        status_filter="completed"
    )
    
    for i, bookmark in enumerate(bookmarks, 1):
        print(f"\n   {i}. {bookmark['clean_title']}")
        print(f"      URL: {bookmark['url'][:60]}...")
        print(f"      Categoría: {bookmark.get('category', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("✅ Ejemplos completados!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar a la API")
        print("   Asegúrate de que el servidor esté corriendo:")
        print("   docker-compose up -d")
    except Exception as e:
        print(f"❌ Error: {e}")
