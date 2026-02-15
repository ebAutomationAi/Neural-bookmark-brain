"""
Tests para verificar rate limiting y configuración del scraper
"""
import pytest
import asyncio
from datetime import datetime
from app.services.scraper import ResilientScraper
from app.config import get_settings

settings = get_settings()


@pytest.mark.asyncio
async def test_rate_limiting():
    """Verifica que el rate limiting funciona correctamente"""
    scraper = ResilientScraper()
    
    # Primera petición - no debería esperar
    start1 = datetime.now()
    await scraper._rate_limit()
    duration1 = (datetime.now() - start1).total_seconds()
    
    assert duration1 < 0.1, "Primera petición no debería tener delay"
    
    # Segunda petición - debería esperar el delay configurado
    start2 = datetime.now()
    await scraper._rate_limit()
    duration2 = (datetime.now() - start2).total_seconds()
    
    expected_delay = settings.SCRAPER_DELAY_BETWEEN_REQUESTS
    assert duration2 >= expected_delay * 0.9, f"Debería esperar al menos {expected_delay}s"
    assert duration2 <= expected_delay * 1.2, f"No debería esperar más de {expected_delay * 1.2}s"


def test_scraper_configuration():
    """Verifica que todas las configuraciones del scraper están presentes"""
    scraper = ResilientScraper()
    
    # Verificar que todas las configuraciones están cargadas
    assert scraper.timeout > 0, "Timeout debe ser > 0"
    assert scraper.max_retries > 0, "Max retries debe ser > 0"
    assert scraper.max_redirects > 0, "Max redirects debe ser > 0"
    assert scraper.delay_between_requests >= 0, "Delay debe ser >= 0"
    
    # Verificar valores por defecto razonables
    assert scraper.timeout <= 60, "Timeout no debería ser excesivo"
    assert scraper.max_retries <= 10, "Max retries no debería ser excesivo"
    assert scraper.max_redirects <= 20, "Max redirects no debería ser excesivo"
    
    print(f"✅ Configuración del scraper:")
    print(f"   • Timeout: {scraper.timeout}s")
    print(f"   • Max retries: {scraper.max_retries}")
    print(f"   • Max redirects: {scraper.max_redirects}")
    print(f"   • Delay entre peticiones: {scraper.delay_between_requests}s")


@pytest.mark.asyncio
async def test_multiple_rate_limited_calls():
    """Verifica rate limiting con múltiples llamadas consecutivas"""
    scraper = ResilientScraper()
    
    start = datetime.now()
    
    # Hacer 3 llamadas
    for i in range(3):
        await scraper._rate_limit()
    
    total_duration = (datetime.now() - start).total_seconds()
    expected_minimum = settings.SCRAPER_DELAY_BETWEEN_REQUESTS * 2  # 2 delays (entre 3 calls)
    
    assert total_duration >= expected_minimum * 0.9, \
        f"Debería tomar al menos {expected_minimum}s, tomó {total_duration}s"
    
    print(f"✅ 3 peticiones con rate limiting tomaron {total_duration:.2f}s")


if __name__ == "__main__":
    # Ejecutar tests manualmente
    print("🧪 Ejecutando tests de rate limiting...\n")
    
    test_scraper_configuration()
    print()
    
    asyncio.run(test_rate_limiting())
    print("✅ Test de rate limiting básico pasado\n")
    
    asyncio.run(test_multiple_rate_limited_calls())
    print("\n✅ Todos los tests pasaron!")
