# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List

class Settings(BaseSettings):
    # --- Base de Datos ---
    DATABASE_URL: str = "postgresql+asyncpg://bookmark_user:bookmark_pass_2024@127.0.0.1:5432/neural_bookmarks"
    EMBEDDING_DIMENSION: int = 384

    # --- API Keys ---
    GROQ_API_KEY: str
    
    # --- Configuración del Scraper ---
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    SCRAPER_TIMEOUT: int = 30
    SCRAPER_MAX_RETRIES: int = 3
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
    
    # --- Pydantic V2 Config ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings():
    return Settings()

