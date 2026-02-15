# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator
from functools import lru_cache
from typing import List
import os

class Settings(BaseSettings):
    # --- Base de Datos ---
    DATABASE_URL: str = "postgresql+asyncpg://bookmark_user:bookmark_pass_2024@127.0.0.1:5432/neural_bookmarks"
    EMBEDDING_DIMENSION: int = 384

    # --- API Keys ---
    GROQ_API_KEY: str
    
    @field_validator('GROQ_API_KEY')
    @classmethod
    def validate_groq_api_key(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError(
                "❌ GROQ_API_KEY no está configurada.\n"
                "Por favor, añade GROQ_API_KEY=tu_clave en el archivo .env\n"
                "Obtén tu API key en: https://console.groq.com/keys"
            )
        return v
    
    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError(
                "❌ DATABASE_URL no está configurada.\n"
                "Por favor, añade DATABASE_URL en el archivo .env\n"
                "Ejemplo: DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname"
            )
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError(
                "❌ DATABASE_URL debe comenzar con 'postgresql://' o 'postgresql+asyncpg://'\n"
                f"URL actual: {v}"
            )
        return v
    
    # --- Configuración del Scraper ---
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    SCRAPER_TIMEOUT: int = 30
    SCRAPER_MAX_RETRIES: int = 3
    SCRAPER_DELAY_BETWEEN_REQUESTS: float = 1.0  # Segundos entre peticiones
    SCRAPER_MAX_REDIRECTS: int = 5  # Máximo número de redirecciones
    local_domains_list: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    
    # --- Configuración de IA y Agentes ---
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    LLM_MODEL_NAME: str = "llama-3.1-8b-instant"
    GROQ_MODEL: str = "llama-3.1-8b-instant"  # <--- Faltaba este campo
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # --- Seguridad y Clasificación ---
    nsfw_keywords_list: List[str] = ["porn", "sex", "xxx", "nude", "casino", "gambling"]
    nsfw_domains_list: List[str] = ["pornhub.com", "xvideos.com"]
    ENABLE_SAFETY_FILTER: bool = True
    
    # --- Rate Limiting ---
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_SEARCH: str = "10/minute"  # Búsquedas
    RATE_LIMIT_CREATE: str = "5/minute"   # Crear bookmarks
    RATE_LIMIT_GLOBAL: str = "100/minute" # Límite global por IP
    
    # --- Pydantic V2 Config ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings():
    """
    Obtiene la configuración de la aplicación.
    Valida que todas las variables de entorno necesarias estén presentes.
    """
    try:
        # Verificar que existe el archivo .env
        env_file = ".env"
        if not os.path.exists(env_file):
            print(f"⚠️  Advertencia: No se encontró el archivo {env_file}")
            print(f"   Asegúrate de crear un archivo .env con las variables necesarias")
            print(f"   Puedes copiar .env.example si existe")
        
        return Settings()
    
    except ValueError as e:
        print("\n" + "="*60)
        print("❌ ERROR DE CONFIGURACIÓN")
        print("="*60)
        print(str(e))
        print("="*60 + "\n")
        raise
    
    except Exception as e:
        print("\n" + "="*60)
        print("❌ ERROR CARGANDO CONFIGURACIÓN")
        print("="*60)
        print(f"Error: {e}")
        print("\nVerifica que:")
        print("1. El archivo .env existe en la raíz del proyecto")
        print("2. Todas las variables requeridas están definidas")
        print("3. El formato de las variables es correcto")
        print("="*60 + "\n")
        raise