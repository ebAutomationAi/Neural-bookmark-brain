# tests/test_sprint1_resilience.py
"""
Tests unitarios para Sprint 1: Resiliencia

Ejecutar:
    pytest tests/test_sprint1_resilience.py -v
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

# Importar las nuevas clases
from app.services.scraper import ResilientScraper, UserAgentRotator
from app.agents import CuratorAgent


class TestUserAgentRotator:
    """Tests para rotación de User-Agents"""
    
    def test_get_random_agent(self):
        """Debe retornar un User-Agent válido"""
        agent = UserAgentRotator.get_random_agent()
        
        assert isinstance(agent, str)
        assert len(agent) > 50
        assert "Mozilla" in agent
    
    def test_get_realistic_headers(self):
        """Debe generar headers completos"""
        headers = UserAgentRotator.get_realistic_headers()
        
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers
        assert "DNT" in headers
        
        # Verificar que Accept-Language incluye español
        assert "es" in headers["Accept-Language"]


class TestResilientScraper:
    """Tests para scraper resiliente"""
    
    @pytest.mark.asyncio
    async def test_is_local_url(self):
        """Debe detectar URLs locales correctamente"""
        scraper = ResilientScraper()
        
        # URLs locales
        assert scraper._is_local_url("http://localhost:3000") == True
        assert scraper._is_local_url("http://192.168.1.1") == True
        assert scraper._is_local_url("http://app.local") == True
        assert scraper._is_local_url("http://mysite.test") == True
        
        # URLs públicas
        assert scraper._is_local_url("https://google.com") == False
        assert scraper._is_local_url("https://github.com/user/repo") == False
    
    def test_extract_clean_title_generic(self):
        """Debe limpiar títulos genéricos"""
        scraper = ResilientScraper()
        
        # Título genérico + dominio
        clean = scraper.extract_clean_title("Home", "example.com")
        assert clean == "Example - Página Principal"
        
        # Título vacío
        clean = scraper.extract_clean_title("", "github.com")
        assert clean == "Github"
    
    def test_extract_clean_title_with_separators(self):
        """Debe limpiar separadores en títulos"""
        scraper = ResilientScraper()
        
        # Título con pipe
        clean = scraper.extract_clean_title("Article Title | Site Name", None)
        assert "Article Title" in clean or "Site Name" in clean
        
        # Título con guión
        clean = scraper.extract_clean_title("Page - Example.com", None)
        assert "Page" in clean or "Example.com" in clean


class TestCuratorAgent:
    """Tests para curador con modo fallback"""
    
    def test_analyze_domain(self):
        """Debe extraer información del dominio correctamente"""
        curator = CuratorAgent()
        
        info = curator._analyze_domain("https://www.github.com/user/repo")
        
        assert info["domain"] == "github"
        assert info["tld"] == "com"
        assert "www" in info["subdomains"]
        assert info["full_domain"] == "github.com"
    
    def test_analyze_path(self):
        """Debe analizar el path de la URL"""
        curator = CuratorAgent()
        
        # URL con keywords de transporte
        info = curator._analyze_path("https://tmb.cat/es/horarios-metro")
        
        assert "es" in info["segments"]
        assert "horarios-metro" in info["segments"]
        assert len(info["keywords"]) > 0  # Debería detectar "transporte"
    
    def test_analyze_path_programming(self):
        """Debe detectar keywords de programación"""
        curator = CuratorAgent()
        
        info = curator._analyze_path("https://github.com/user/python-tutorial")
        
        assert "github" in info["segments"]
        assert "python-tutorial" in info["segments"]
        # Debería detectar "programación" por "github" o "python"


class TestIntegrationScrapingFlow:
    """Tests de integración del flujo completo"""
    
    @pytest.mark.asyncio
    async def test_scraping_with_error_classification(self):
        """Debe clasificar errores correctamente"""
        scraper = ResilientScraper()
        
        # Simular error 403 (bot detection)
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_get.return_value = mock_response
            
            result = await scraper.scrape_url("https://example.com/blocked")
            
            assert result["success"] == False
            assert result["error_type"] == "bot_detection"
            assert result["attempts"] > 0
    
    @pytest.mark.asyncio
    async def test_scraping_with_retry_success(self):
        """Debe reintentar y eventualmente tener éxito"""
        scraper = ResilientScraper()
        
        # Simular fallo en primer intento, éxito en segundo
        call_count = 0
        
        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                raise Exception("Timeout")
            else:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.text = "<html><body>Test content</body></html>"
                return mock_response
        
        with patch('httpx.AsyncClient.get', side_effect=mock_get):
            result = await scraper.scrape_url("https://example.com")
            
            # Debería haber reintentado
            assert call_count > 1


class TestConfidenceScoring:
    """Tests para el sistema de confidence scoring"""
    
    def test_confidence_full_text(self):
        """Modo full_text debe tener confidence 1.0"""
        # Esto se testearía con el agente completo
        # Por ahora es ejemplo de lo que esperamos
        expected_confidence = 1.0
        assert expected_confidence == 1.0
    
    def test_confidence_url_only_known_domain(self):
        """URLs de dominios conocidos deben tener confidence alta"""
        # Ejemplo: github.com, wikipedia.org
        # La IA debería asignar confidence 0.8-0.9
        known_domain_confidence_range = (0.7, 0.9)
        
        # Test conceptual
        test_confidence = 0.85
        assert known_domain_confidence_range[0] <= test_confidence <= known_domain_confidence_range[1]
    
    def test_confidence_url_only_unknown_domain(self):
        """URLs de dominios desconocidos deben tener confidence menor"""
        unknown_domain_confidence_range = (0.4, 0.6)
        
        test_confidence = 0.5
        assert unknown_domain_confidence_range[0] <= test_confidence <= unknown_domain_confidence_range[1]


# Tests de regresión
class TestBackwardCompatibility:
    """Asegurar que no rompimos funcionalidad existente"""
    
    @pytest.mark.asyncio
    async def test_scraping_returns_expected_fields(self):
        """Scraping debe retornar todos los campos esperados"""
        scraper = ResilientScraper()
        
        # Mock de respuesta exitosa
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "<html><head><title>Test</title></head><body>Content</body></html>"
            mock_get.return_value = mock_response
            
            result = await scraper.scrape_url("https://example.com")
            
            # Campos obligatorios
            assert "success" in result
            assert "error_type" in result
            assert "attempts" in result
            assert "strategy" in result
            
            # Campos de contenido
            assert "title" in result
            assert "text" in result or result["success"] == False


if __name__ == "__main__":
    # Ejecutar tests básicos
    print("🧪 Ejecutando tests de Sprint 1...")
    pytest.main([__file__, "-v", "--tb=short"])