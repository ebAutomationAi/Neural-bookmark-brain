import trafilatura
import httpx
from typing import Optional, Dict
from loguru import logger
from datetime import datetime
import tldextract
from urllib.parse import urlparse

from app.config import get_settings

settings = get_settings()


class ContentScraper:
    """Servicio de scraping usando Trafilatura"""
    
    def __init__(self):
        self.timeout = settings.SCRAPER_TIMEOUT
        self.user_agent = settings.SCRAPER_USER_AGENT
        self.max_retries = settings.SCRAPER_MAX_RETRIES
    
    async def scrape_url(self, url: str) -> Dict[str, any]:
        """
        Extrae contenido de una URL
        
        Returns:
            Dict con: success, title, text, html, language, error
        """
        result = {
            "success": False,
            "title": None,
            "text": None,
            "html": None,
            "language": None,
            "word_count": 0,
            "domain": None,
            "error": None,
        }
        
        try:
            # Extraer dominio
            extracted = tldextract.extract(url)
            result["domain"] = f"{extracted.domain}.{extracted.suffix}"
            
            # Verificar si es URL local
            if self._is_local_url(url):
                result["error"] = "URL local detectada - requiere captura manual"
                return result
            
            # Descargar contenido
            logger.info(f"Descargando contenido de: {url}")
            
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": self.user_agent}
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text
                result["html"] = html
            
            # Extraer contenido con Trafilatura
            downloaded = trafilatura.fetch_url(url)
            
            if downloaded:
                # Extraer texto limpio
                text = trafilatura.extract(
                    downloaded,
                    include_comments=False,
                    include_tables=True,
                    no_fallback=False,
                )
                
                # Extraer metadata
                metadata = trafilatura.extract_metadata(downloaded)
                
                if text:
                    result["success"] = True
                    result["text"] = text
                    result["word_count"] = len(text.split())
                    
                    if metadata:
                        result["title"] = metadata.title
                        result["language"] = metadata.language
                        
                        logger.info(
                            f"Scraping exitoso: {url} - "
                            f"{result['word_count']} palabras"
                        )
                else:
                    result["error"] = "No se pudo extraer texto del contenido"
                    logger.warning(f"No se extrajo texto de: {url}")
            else:
                result["error"] = "No se pudo descargar el contenido"
                logger.warning(f"Descarga fallida: {url}")
        
        except httpx.TimeoutException:
            result["error"] = f"Timeout después de {self.timeout}s"
            logger.error(f"Timeout en: {url}")
        
        except httpx.HTTPStatusError as e:
            result["error"] = f"HTTP {e.response.status_code}"
            logger.error(f"Error HTTP {e.response.status_code} en: {url}")
        
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error scraping {url}: {e}")
        
        return result
    
    def _is_local_url(self, url: str) -> bool:
        """Verifica si la URL es local (.test, .local, localhost, etc.)"""
        try:
            parsed = urlparse(url.lower())
            hostname = parsed.hostname or parsed.netloc
            
            # Verificar contra dominios locales configurados
            for local_domain in settings.local_domains_list:
                if local_domain in hostname:
                    return True
            
            return False
        
        except Exception as e:
            logger.warning(f"Error verificando URL local {url}: {e}")
            return False
    
    def extract_clean_title(self, original_title: str, domain: str = None) -> str:
        """
        Limpia títulos genéricos como 'Home', 'Index', etc.
        
        Args:
            original_title: Título original del bookmark
            domain: Dominio para mejorar el título
        
        Returns:
            Título limpio y descriptivo
        """
        generic_titles = {
            "home", "index", "welcome", "inicio", "página principal",
            "main page", "default", "untitled", "new tab", "homepage"
        }
        
        title_lower = original_title.lower().strip()
        
        # Si el título es genérico y tenemos dominio
        if title_lower in generic_titles and domain:
            # Capitalizar dominio como título
            clean_domain = domain.replace("-", " ").replace("_", " ").title()
            return f"{clean_domain} - Página Principal"
        
        # Si el título está vacío
        if not original_title.strip():
            return domain.title() if domain else "Título Desconocido"
        
        # Limpiar separadores comunes
        title_clean = original_title.strip()
        
        # Remover pipes y guiones al final
        for separator in ["|", "-", "—", "–"]:
            if separator in title_clean:
                parts = title_clean.split(separator)
                # Tomar la parte más larga
                title_clean = max(parts, key=len).strip()
        
        return title_clean


# Singleton
scraper = ContentScraper()
