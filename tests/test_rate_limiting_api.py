"""
Test para verificar rate limiting en la API
"""
import asyncio
import httpx
import pytest
from datetime import datetime


BASE_URL = "http://localhost:8000"


async def test_search_rate_limit():
    """
    Test que verifica que el rate limit de búsqueda funciona
    Configurado: 10/minute
    """
    print("\n🧪 Testeando rate limit de búsqueda (10/minute)...")
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Hacer 10 peticiones (debería funcionar)
        successful = 0
        for i in range(1, 11):
            try:
                response = await client.post("/search", json={
                    "query": f"test query {i}",
                    "limit": 5,
                    "include_nsfw": False
                })
                if response.status_code == 200:
                    successful += 1
                    print(f"   ✅ Petición {i}/10: OK")
                else:
                    print(f"   ❌ Petición {i}/10: {response.status_code}")
            except Exception as e:
                print(f"   ❌ Petición {i}/10: Error - {e}")
        
        print(f"\n   📊 {successful}/10 peticiones exitosas")
        
        # Hacer una petición más (debería ser bloqueada)
        print("\n   🚫 Intentando petición #11 (debería fallar)...")
        try:
            response = await client.post("/search", json={
                "query": "test over limit",
                "limit": 5
            })
            
            if response.status_code == 429:
                print(f"   ✅ Correctamente bloqueada con 429 Too Many Requests")
                print(f"   📝 Mensaje: {response.json()}")
                return True
            else:
                print(f"   ⚠️  Debería haber sido bloqueada pero obtuvo: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False


async def test_create_rate_limit():
    """
    Test que verifica que el rate limit de creación funciona
    Configurado: 5/minute
    """
    print("\n🧪 Testeando rate limit de creación (5/minute)...")
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Hacer 5 peticiones
        successful = 0
        for i in range(1, 6):
            try:
                response = await client.post("/bookmarks", json={
                    "url": f"https://example.com/page{i}",
                    "original_title": f"Test Page {i}"
                })
                # 409 es también aceptable (bookmark duplicado)
                if response.status_code in [200, 201, 409]:
                    successful += 1
                    status = "OK" if response.status_code in [200, 201] else "Duplicado"
                    print(f"   ✅ Petición {i}/5: {status}")
                else:
                    print(f"   ❌ Petición {i}/5: {response.status_code}")
            except Exception as e:
                print(f"   ❌ Petición {i}/5: Error - {e}")
        
        print(f"\n   📊 {successful}/5 peticiones exitosas")
        
        # Hacer una más (debería ser bloqueada)
        print("\n   🚫 Intentando petición #6 (debería fallar)...")
        try:
            response = await client.post("/bookmarks", json={
                "url": "https://example.com/over-limit",
                "original_title": "Over Limit"
            })
            
            if response.status_code == 429:
                print(f"   ✅ Correctamente bloqueada con 429 Too Many Requests")
                return True
            else:
                print(f"   ⚠️  Debería haber sido bloqueada pero obtuvo: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False


async def test_health_no_rate_limit():
    """
    Verifica que endpoints sin rate limit específico funcionan
    """
    print("\n🧪 Testeando endpoint sin rate limit (/health)...")
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Health check no debería tener rate limit específico
        # Solo el global (100/minute)
        for i in range(1, 11):
            response = await client.get("/health")
            if response.status_code == 200:
                print(f"   ✅ Petición {i}/10: OK")
            else:
                print(f"   ❌ Petición {i}/10: {response.status_code}")
                return False
    
    print("   ✅ Todas las peticiones pasaron (sin rate limit específico)")
    return True


def main():
    """Función principal"""
    print("="*60)
    print("🔒 TEST DE RATE LIMITING DE LA API")
    print("="*60)
    print("\n⚠️  IMPORTANTE: Asegúrate de que la API esté corriendo en")
    print(f"   {BASE_URL}")
    print("\n   Inicia la API con: uvicorn app.main:app --reload\n")
    
    input("Presiona Enter para continuar...")
    
    try:
        # Test 1: Health check
        result1 = asyncio.run(test_health_no_rate_limit())
        
        # Test 2: Search rate limit
        result2 = asyncio.run(test_search_rate_limit())
        
        # Esperar un poco antes del siguiente test
        print("\n⏳ Esperando 5 segundos antes del siguiente test...")
        asyncio.run(asyncio.sleep(5))
        
        # Test 3: Create rate limit
        result3 = asyncio.run(test_create_rate_limit())
        
        print("\n" + "="*60)
        print("📊 RESUMEN DE TESTS")
        print("="*60)
        print(f"   Health endpoint: {'✅ PASS' if result1 else '❌ FAIL'}")
        print(f"   Search rate limit: {'✅ PASS' if result2 else '❌ FAIL'}")
        print(f"   Create rate limit: {'✅ PASS' if result3 else '❌ FAIL'}")
        print("="*60)
        
        if all([result1, result2, result3]):
            print("\n✅ Todos los tests pasaron!")
            return 0
        else:
            print("\n⚠️  Algunos tests fallaron")
            return 1
    
    except httpx.ConnectError:
        print("\n❌ Error: No se pudo conectar a la API")
        print(f"   Verifica que la API esté corriendo en {BASE_URL}")
        return 1
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
