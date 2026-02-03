from typing import Tuple, Optional
from loguru import logger
from urllib.parse import urlparse
import re

from app.config import get_settings

settings = get_settings()


class SafetyClassifier:
    """Clasificador de contenido NSFW/Adult basado en keywords y dominios"""
    
    def __init__(self):
        self.nsfw_keywords = settings.nsfw_keywords_list
        self.nsfw_domains = settings.nsfw_domains_list
    
    def classify(
        self,
        url: str,
        title: str = "",
        text: str = "",
    ) -> Tuple[bool, Optional[str]]:
        """
        Clasifica si el contenido es NSFW
        
        Args:
            url: URL del bookmark
            title: Título del contenido
            text: Texto extraído del contenido
        
        Returns:
            Tuple: (is_nsfw: bool, reason: str)
        """
        # 1. Verificar dominio
        is_nsfw_domain, domain_reason = self._check_domain(url)
        if is_nsfw_domain:
            return True, domain_reason
        
        # 2. Verificar URL
        is_nsfw_url, url_reason = self._check_url(url)
        if is_nsfw_url:
            return True, url_reason
        
        # 3. Verificar título
        if title:
            is_nsfw_title, title_reason = self._check_text(title, "título")
            if is_nsfw_title:
                return True, title_reason
        
        # 4. Verificar texto (sample)
        if text:
            # Solo analizar primeros 1000 caracteres para eficiencia
            text_sample = text[:1000]
            is_nsfw_text, text_reason = self._check_text(text_sample, "contenido")
            if is_nsfw_text:
                return True, text_reason
        
        return False, None
    
    def _check_domain(self, url: str) -> Tuple[bool, Optional[str]]:
        """Verifica si el dominio está en la lista NSFW"""
        try:
            parsed = urlparse(url.lower())
            hostname = parsed.hostname or parsed.netloc
            
            for nsfw_domain in self.nsfw_domains:
                if nsfw_domain in hostname:
                    logger.warning(f"Dominio NSFW detectado: {hostname}")
                    return True, f"Dominio NSFW: {nsfw_domain}"
            
            return False, None
        
        except Exception as e:
            logger.error(f"Error verificando dominio NSFW: {e}")
            return False, None
    
    def _check_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """Verifica si la URL contiene keywords NSFW"""
        url_lower = url.lower()
        
        for keyword in self.nsfw_keywords:
            # Buscar keyword como palabra completa (no substring)
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, url_lower):
                logger.warning(f"Keyword NSFW en URL: {keyword}")
                return True, f"Keyword NSFW en URL: {keyword}"
        
        return False, None
    
    def _check_text(self, text: str, source: str) -> Tuple[bool, Optional[str]]:
        """Verifica si el texto contiene keywords NSFW"""
        text_lower = text.lower()
        
        # Contador de coincidencias
        matches = 0
        found_keywords = []
        
        for keyword in self.nsfw_keywords:
            # Buscar keyword como palabra completa
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                matches += 1
                found_keywords.append(keyword)
        
        # Umbral: si hay 2+ keywords, marcar como NSFW
        if matches >= 2:
            logger.warning(f"Keywords NSFW en {source}: {found_keywords}")
            return True, f"Keywords NSFW en {source}: {', '.join(found_keywords[:3])}"
        
        return False, None
    
    def add_keyword(self, keyword: str):
        """Añade keyword NSFW en runtime"""
        if keyword.lower() not in self.nsfw_keywords:
            self.nsfw_keywords.append(keyword.lower())
            logger.info(f"Keyword NSFW añadida: {keyword}")
    
    def add_domain(self, domain: str):
        """Añade dominio NSFW en runtime"""
        if domain.lower() not in self.nsfw_domains:
            self.nsfw_domains.append(domain.lower())
            logger.info(f"Dominio NSFW añadido: {domain}")


# Singleton
classifier = SafetyClassifier()
