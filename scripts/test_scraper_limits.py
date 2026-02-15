#!/usr/bin/env python3
"""
Script para probar las limitaciones del scraper
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Añadir el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.services.scraper import ResilientScraper
from app.config import get_settings

settings = get_settings()


async def test_rate_limiting():
    """Test básico de rate limiting"""
    print("🕐 Testeando rate limiting...\n")
    
    scraper = ResilientScraper()
    
    print(f"⚙️  Configuración actual:")
    print(f"   • Delay entre peticiones: {scraper.delay_between_requests}s")
    print(f"   • Timeout: {scraper.timeout}s")
    print(f"   • Max redirects: {scraper.max_redirects}")
    print(f"   • Max retries: {scraper.max_retries}\n")
    
    # Simular 3 peticiones
    print("📡 Simulando 3 peticiones consecutivas...\n")
    
    for i in range(1, 4):
        start = datetime.now()
        await scraper._rate_limit()
        duration = (datetime.now() - start).total_seconds()
        
        print(f"   Petición {i}: {duration:.3f}s de espera")
    
    print("\n✅ Rate limiting funcionando correctamente")


async def test_real_url(url: str):
    """Test con URL real"""
    print(f"\n🌐 Testeando scraping de URL real: {url}\n")
    
    scraper = ResilientScraper()
    
    start = datetime.now()
    result = await scraper.scrape_url(url)
    duration = (datetime.now() - start).total_seconds()
    
    print(f"\n📊 Resultado del scraping ({duration:.2f}s):")
    print(f"   • Success: {result['success']}")
    print(f"   • Strategy: {result.get('strategy', 'N/A')}")
    print(f"   • Attempts: {result.get('attempts', 0)}")
    print(f"   • Error type: {result.get('error_type', 'N/A')}")
    
    if result['success']:
        print(f"   • Title: {result.get('title', 'N/A')[:50]}...")
        print(f"   • Word count: {result.get('word_count', 0)}")
        print(f"   • Domain: {result.get('domain', 'N/A')}")
    else:
        print(f"   • Error: {result.get('error_message', 'N/A')[:100]}")


async def test_multiple_urls():
    """Test con múltiples URLs para verificar rate limiting"""
    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://www.python.org",
    ]
    
    print(f"\n🔄 Testeando {len(urls)} URLs con rate limiting...\n")
    
    scraper = ResilientScraper()
    
    overall_start = datetime.now()
    
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Scraping: {url}")
        start = datetime.now()
        
        result = await scraper.scrape_url(url)
        
        duration = (datetime.now() - start).total_seconds()
        status = "✅" if result['success'] else "❌"
        
        print(f"    {status} {duration:.2f}s - {result.get('strategy', 'N/A')}")
    
    total_duration = (datetime.now() - overall_start).total_seconds()
    expected_minimum = scraper.delay_between_requests * (len(urls) - 1)
    
    print(f"\n⏱️  Tiempo total: {total_duration:.2f}s")
    print(f"    (mínimo esperado con rate limiting: {expected_minimum:.2f}s)")
    
    if total_duration >= expected_minimum * 0.9:
        print("✅ Rate limiting está funcionando correctamente")
    else:
        print("⚠️  Rate limiting podría no estar funcionando como esperado")


def main():
    """Función principal"""
    print("="*60)
    print("🧪 TEST DE LIMITACIONES DEL SCRAPER")
    print("="*60)
    
    # Test 1: Rate limiting básico
    asyncio.run(test_rate_limiting())
    
    # Test 2: URL real (opcional)
    if len(sys.argv) > 1:
        url = sys.argv[1]
        asyncio.run(test_real_url(url))
    
    # Test 3: Múltiples URLs
    asyncio.run(test_multiple_urls())
    
    print("\n" + "="*60)
    print("✅ Tests completados")
    print("="*60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print("Uso:")
        print("  python scripts/test_scraper_limits.py              # Tests básicos")
        print("  python scripts/test_scraper_limits.py <URL>        # Incluir test con URL específica")
        print("\nEjemplo:")
        print("  python scripts/test_scraper_limits.py https://example.com")
        sys.exit(0)
    
    main()
