# app/utils/validators.py - VERSIÓN CORREGIDA (parcial - solo TextValidator)

import validators
from typing import Optional, Tuple
from urllib.parse import urlparse
import re
from loguru import logger


class URLValidator:
    """Validador de URLs"""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Valida si una URL es válida"""
        if not url or not url.strip():
            return False
        
        # Validación básica con validators
        return validators.url(url.strip()) is True
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """Normaliza una URL (añade https:// si falta, etc.)"""
        url = url.strip()
        
        # Si no tiene esquema, añadir https://
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
        
        return url
    
    @staticmethod
    def extract_domain(url: str) -> Optional[str]:
        """Extrae el dominio de una URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc or parsed.hostname
        except Exception as e:
            logger.error(f"Error extrayendo dominio de {url}: {e}")
            return None
    
    @staticmethod
    def validate_and_normalize(url: str) -> Tuple[bool, str, Optional[str]]:
        """
        Valida y normaliza una URL
        
        Returns:
            Tuple: (is_valid, normalized_url, error_message)
        """
        if not url or not url.strip():
            return False, url, "URL vacía"
        
        # Normalizar
        normalized = URLValidator.normalize_url(url)
        
        # Validar
        if not URLValidator.is_valid_url(normalized):
            return False, url, "URL inválida"
        
        return True, normalized, None


class TextValidator:
    """Validador de texto y contenido"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Limpia texto de caracteres especiales y espacios extra
        CORREGIDO: Mantiene espacios simples entre palabras
        """
        if not text:
            return ""
        
        # 1. Remover caracteres de control (excepto espacios normales)
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # 2. Convertir tabs y newlines a espacios
        text = text.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
        
        # 3. Normalizar múltiples espacios a uno solo
        text = re.sub(r' +', ' ', text)
        
        # 4. Strip espacios al inicio/final
        return text.strip()
    
    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = "...") -> str:
        """Trunca texto a longitud máxima"""
        if not text or len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def extract_first_sentence(text: str) -> str:
        """Extrae la primera oración de un texto"""
        if not text:
            return ""
        
        # Buscar primer punto, signo de exclamación o interrogación
        match = re.search(r'[.!?]', text)
        
        if match:
            return text[:match.end()].strip()
        
        # Si no hay puntuación, retornar primeras 100 palabras
        words = text.split()
        if len(words) > 100:
            return ' '.join(words[:100]) + '...'
        
        return text
    
    @staticmethod
    def is_meaningful_text(text: str, min_words: int = 10) -> bool:
        """Verifica si el texto es significativo"""
        if not text:
            return False
        
        words = text.split()
        return len(words) >= min_words


class DataValidator:
    """Validador de datos generales"""
    
    @staticmethod
    def validate_tags(tags: list) -> list:
        """Valida y limpia lista de tags"""
        if not tags:
            return []
        
        cleaned_tags = []
        for tag in tags:
            if isinstance(tag, str):
                tag_clean = tag.strip().lower()
                if tag_clean and len(tag_clean) > 1:
                    cleaned_tags.append(tag_clean)
        
        # Remover duplicados manteniendo orden
        seen = set()
        unique_tags = []
        for tag in cleaned_tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)
        
        return unique_tags
    
    @staticmethod
    def validate_category(category: str, valid_categories: list) -> Optional[str]:
        """Valida que una categoría esté en la lista válida"""
        if not category:
            return None
        
        category_clean = category.strip().title()
        
        if category_clean in valid_categories:
            return category_clean
        
        # Buscar coincidencia parcial
        for valid_cat in valid_categories:
            if category_clean.lower() in valid_cat.lower():
                return valid_cat
        
        return "Otros"  # Categoría por defecto
    
    @staticmethod
    def validate_embedding(embedding: list, expected_dim: int) -> bool:
        """Valida que un embedding tenga la dimensión correcta"""
        if not embedding:
            return False
        
        if not isinstance(embedding, list):
            return False
        
        if len(embedding) != expected_dim:
            return False
        
        # Verificar que todos sean números
        try:
            all(isinstance(x, (int, float)) for x in embedding)
            return True
        except:
            return False


# Categorías válidas del sistema
VALID_CATEGORIES = [
    "Tecnología",
    "Negocios",
    "Educación",
    "Entretenimiento",
    "Salud",
    "Ciencia",
    "Arte",
    "Deportes",
    "Noticias",
    "Programación",
    "Diseño",
    "Marketing",
    "Finanzas",
    "Productividad",
    "Otros"
]