import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import Dict, Tuple, Optional
from loguru import logger

class URLCleaner:
    """Limpia URLs de parámetros de tracking para deduplicación"""
    
    # Patrones de parámetros de tracking comunes
    TRACKING_PARAMS = {
        # Google Analytics
        '_gl', '_ga', '_gid', '_gat', 'ga', 'utm_source', 'utm_medium', 
        'utm_campaign', 'utm_term', 'utm_content', 'utm_id', 'utm_source_platform',
        'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        # Facebook
        'fbclid', 'ref', 'fb_source', 'fb_action_ids', 'fb_action_types',
        # Google Ads
        'gclid', 'gclsrc',
        # Microsoft
        'msclkid',
        # Twitter
        'twclid',
        # LinkedIn
        'li_fat_id', 'trk',
        # Outbrain
        'ob_click_id',
        # Taboola
        'taboola',
        # Reddit
        'rdt_cid',
        # Otros comunes
        'ref_src', 'ref_url', 'cmpid', 'ncid', '_bta_tid', '_bta_c', 'mc_cid',
        'mc_eid', 'pk_campaign', 'pk_kwd', 'piwik_campaign', 'piwik_kwd',
        'mtm_campaign', 'mtm_keyword', 'mtm_source', 'mtm_medium',
    }
    
    @staticmethod
    def clean_url(url: str) -> Tuple[str, Dict[str, any]]:
        """
        Limpia una URL de parámetros de tracking
        
        Args:
            url: URL original con posibles parámetros de tracking
            
        Returns:
            Tuple: (url_limpia, dict_con_parametros_tracking)
        """
        try:
            # Manejar URLs vacías o None
            if not url or not isinstance(url, str):
                return url, {}
            
            parsed = urlparse(url)
            
            # Si no hay query string, retornar URL original (sin trailing slash)
            if not parsed.query:
                cleaned_url = url.rstrip('/') if url.endswith('/') and not url.endswith('://') else url
                return cleaned_url, {}
            
            # Parsear todos los parámetros
            all_params = parse_qs(parsed.query, keep_blank_values=True)
            
            # Separar parámetros de tracking de parámetros funcionales
            tracking_params = {}
            functional_params = {}
            
            for key, values in all_params.items():
                if key in URLCleaner.TRACKING_PARAMS:
                    tracking_params[key] = values[0] if len(values) == 1 else values
                else:
                    functional_params[key] = values
            
            # Reconstruir URL con solo parámetros funcionales
            cleaned_query = urlencode(functional_params, doseq=True)
            
            # Reconstruir URL completa
            cleaned_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path.rstrip('/'),  # Eliminar trailing slash en el path
                parsed.params,
                cleaned_query,
                parsed.fragment
            ))
            
            # Si la URL limpia es igual a la original (ignorando trailing slash), retornar original
            original_normalized = url.rstrip('/')
            cleaned_normalized = cleaned_url.rstrip('/')
            
            if cleaned_normalized == original_normalized:
                return url, {}
            
            logger.debug(
                f"URL limpiada: {url[:60]}... → {cleaned_url[:60]}... "
                f"(tracking params: {len(tracking_params)})"
            )
            
            return cleaned_url, tracking_params
            
        except Exception as e:
            logger.warning(f"Error limpiando URL {url[:80]}: {e}")
            return url, {}
    
    @staticmethod
    def has_tracking_params(url: str) -> bool:
        """Verifica si una URL contiene parámetros de tracking"""
        try:
            if not url or not isinstance(url, str):
                return False
            
            parsed = urlparse(url)
            if not parsed.query:
                return False
            
            params = parse_qs(parsed.query)
            return any(key in URLCleaner.TRACKING_PARAMS for key in params.keys())
        except:
            return False
    
    @staticmethod
    def extract_domain(url: str) -> str:
        """Extrae el dominio de una URL"""
        try:
            if not url or not isinstance(url, str):
                return ""
            
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ""


# Singleton
url_cleaner = URLCleaner()