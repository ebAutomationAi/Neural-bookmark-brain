# app/services/scraper.py - VERSIÓN RESILIENTE

import trafilatura
import httpx
from typing import Optional, Dict, Tuple
from loguru import logger
from datetime import datetime
import tldextract
from urllib.parse import urlparse
import random
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)

from app.config import get_settings

settings = get_settings()


class ScrapingError(Exception):
    """Error base de scraping"""
    pass


class BotDetectionError(ScrapingError):
    """Error 403 - Detectado como bot"""
    pass


class RateLimitError(ScrapingError):
    """Error 429 - Rate limited"""
    pass


class TimeoutError(ScrapingError):
    """Timeout de conexión"""
    pass


class UserAgentRotator:
    """Rotación de User-Agents realistas"""
    
    AGENTS = [
        # Chrome Windows (más común)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Firefox Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        # Edge Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.133",
        # Safari macOS (menos común pero realista)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    ]
    
    @classmethod
    def get_random_agent(cls) -> str:
        """Obtiene un User-Agent aleatorio"""
        return random.choice(cls.AGENTS)
    
    @classmethod
    def get_realistic_headers(cls) -> Dict[str, str]:
        """Headers completos que parecen navegador real"""
        return {
            "User-Agent": cls.get_random_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }


class ResilientScraper:
    """Scraper con múltiples estrategias y reintentos"""
    
    def __init__(self):
        self.timeout = settings.SCRAPER_TIMEOUT
        self.max_retries = settings.SCRAPER_MAX_RETRIES
        self.user_agent_rotator = UserAgentRotator()
    
    async def scrape_url(self, url: str) -> Dict:
        """
        Scraping resiliente con múltiples estrategias
        
        Returns:
            Dict con: success, text, title, strategy, error_type, attempts, etc.
        """
        result = {
            "success": False,
            "title": None,
            "text": None,
            "html": None,
            "language": None,
            "word_count": 0,
            "domain": None,
            "strategy": None,
            "error_type": None,
            "error_message": None,
            "attempts": 0,
        }
        
        try:
            # Extraer dominio
            extracted = tldextract.extract(url)
            result["domain"] = f"{extracted.domain}.{extracted.suffix}"
            
            # Verificar si es URL local
            if self._is_local_url(url):
                result["error_type"] = "local_url"
                result["error_message"] = "URL local detectada - requiere captura manual"
                return result
            
            # Estrategia 1: Trafilatura con reintentos
            logger.info(f"[Scraper] Estrategia 1: Trafilatura con reintentos")
            strategy_result = await self._trafilatura_with_retry(url)
            result["attempts"] += strategy_result["attempts"]
            
            if strategy_result["success"]:
                result.update(strategy_result)
                result["strategy"] = "trafilatura_retry"
                logger.info(f"✅ Scraping exitoso con trafilatura: {url}")
                return result
            
            # Si falla con bot detection, intentar con BeautifulSoup básico
            if strategy_result.get("error_type") == "bot_detection":
                logger.warning(f"[Scraper] Bot detection - Intentando estrategia 2: BeautifulSoup")
                bs_result = await self._beautifulsoup_fallback(url)
                result["attempts"] += 1
                
                if bs_result["success"]:
                    result.update(bs_result)
                    result["strategy"] = "beautifulsoup"
                    logger.info(f"✅ Scraping exitoso con BeautifulSoup: {url}")
                    return result
            
            # Si todas las estrategias fallan
            result["error_type"] = strategy_result.get("error_type", "unknown")
            result["error_message"] = strategy_result.get("error_message", "Todas las estrategias fallaron")
            logger.error(f"❌ Scraping fallido: {url} - {result['error_type']}")
        
        except Exception as e:
            result["error_type"] = "unexpected_error"
            result["error_message"] = str(e)
            logger.error(f"❌ Error inesperado en scraping {url}: {e}")
        
        return result
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True
    )
    async def _fetch_with_retry(self, url: str, headers: Dict) -> httpx.Response:
        """Descarga HTML con reintentos automáticos para errores temporales"""
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
        ) as client:
            response = await client.get(url, headers=headers)
            
            # Clasificar errores HTTP
            if response.status_code == 403:
                raise BotDetectionError(f"403 Forbidden - Bot detection: {url}")
            elif response.status_code == 429:
                raise RateLimitError(f"429 Too Many Requests: {url}")
            elif response.status_code >= 500:
                raise httpx.HTTPStatusError(f"Server error {response.status_code}", request=response.request, response=response)
            
            response.raise_for_status()
            return response
    
    async def _trafilatura_with_retry(self, url: str) -> Dict:
        """Estrategia 1: Trafilatura con reintentos inteligentes"""
        result = {
            "success": False,
            "attempts": 0,
            "error_type": None,
            "error_message": None,
        }
        
        for attempt in range(1, self.max_retries + 1):
            result["attempts"] = attempt
            
            try:
                logger.info(f"  Intento {attempt}/{self.max_retries}: Descargando {url}")
                
                # Rotar headers en cada intento
                headers = self.user_agent_rotator.get_realistic_headers()
                
                # Descargar con reintentos
                response = await self._fetch_with_retry(url, headers)
                html = response.text
                
                # Extraer contenido con Trafilatura
                text = trafilatura.extract(
                    html,
                    include_comments=False,
                    include_tables=True,
                    no_fallback=False,
                )
                
                # Extraer metadata
                metadata = trafilatura.extract_metadata(html)
                
                if text and len(text.strip()) > 50:
                    result["success"] = True
                    result["text"] = text
                    result["html"] = html[:10000]  # Limitar tamaño
                    result["word_count"] = len(text.split())
                    
                    if metadata:
                        result["title"] = metadata.title
                        result["language"] = metadata.language
                    
                    return result
                else:
                    logger.warning(f"  Texto extraído muy corto ({len(text) if text else 0} chars)")
                    result["error_type"] = "insufficient_content"
                    result["error_message"] = "Contenido extraído insuficiente"
            
            except BotDetectionError as e:
                result["error_type"] = "bot_detection"
                result["error_message"] = str(e)
                logger.warning(f"  Bot detection detectado en intento {attempt}")
                # No reintentar si es bot detection - pasar a siguiente estrategia
                break
            
            except RateLimitError as e:
                result["error_type"] = "rate_limited"
                result["error_message"] = str(e)
                logger.warning(f"  Rate limited en intento {attempt}")
                # Esperar más tiempo antes de siguiente intento
                if attempt < self.max_retries:
                    import asyncio
                    await asyncio.sleep(10 * attempt)
            
            except httpx.TimeoutException as e:
                result["error_type"] = "timeout"
                result["error_message"] = f"Timeout después de {self.timeout}s"
                logger.warning(f"  Timeout en intento {attempt}")
            
            except httpx.ConnectError as e:
                result["error_type"] = "connection_refused"
                result["error_message"] = "No se pudo conectar al servidor"
                logger.warning(f"  Connection refused en intento {attempt}")
            
            except httpx.HTTPStatusError as e:
                result["error_type"] = "http_error"
                result["error_message"] = f"HTTP {e.response.status_code}"
                logger.warning(f"  HTTP error {e.response.status_code} en intento {attempt}")
            
            except Exception as e:
                result["error_type"] = "unknown"
                result["error_message"] = str(e)
                logger.error(f"  Error inesperado en intento {attempt}: {e}")
        
        return result
    
    async def _beautifulsoup_fallback(self, url: str) -> Dict:
        """Estrategia 2: BeautifulSoup básico (menos detectable)"""
        try:
            from bs4 import BeautifulSoup
            
            headers = self.user_agent_rotator.get_realistic_headers()
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Eliminar scripts y styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extraer texto
            text = soup.get_text(separator=' ', strip=True)
            title = soup.find('title').text if soup.find('title') else ""
            
            # Limpiar texto
            lines = (line.strip() for line in text.splitlines())
            text = '\n'.join(line for line in lines if line)
            
            return {
                "success": True,
                "text": text[:10000],  # Limitar
                "title": title,
                "html": response.text[:10000],
                "word_count": len(text.split()),
            }
        
        except Exception as e:
            return {
                "success": False,
                "error_type": "beautifulsoup_failed",
                "error_message": str(e),
            }
    
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
scraper = ResilientScraper()