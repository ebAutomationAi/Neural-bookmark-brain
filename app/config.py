# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # --- Base de Datos ---
    DATABASE_URL: str = ""
    EMBEDDING_DIMENSION: int = 384

    # --- API Keys ---
    GROQ_API_KEY: str = ""

    # --- CORS ---
    CORS_ORIGINS: str = "*"

    # --- Rate limiting ---
    RATE_LIMIT_GLOBAL: str = "100/minute"
    RATE_LIMIT_SEARCH: str = "10/minute"
    RATE_LIMIT_CREATE: str = "5/minute"

    # --- Configuración del Scraper ---
    SCRAPER_USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    SCRAPER_TIMEOUT: int = 30
    SCRAPER_MAX_RETRIES: int = 3
    SCRAPER_MAX_REDIRECTS: int = 5
    SCRAPER_DELAY_BETWEEN_REQUESTS: float = 1.0

    # FIX: Mantener como str + @property para evitar que pydantic-settings
    # intente deserializar como JSON antes de que el validator pueda actuar.
    # pydantic-settings v2 falla con List[str] + validation_alias cuando el
    # valor en .env es una cadena CSV (no JSON).
    LOCAL_DOMAINS: str = "localhost,127.0.0.1,0.0.0.0"

    # --- Configuración de IA y Agentes ---
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    LLM_MODEL_NAME: str = "llama-3.1-8b-instant"
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # --- Seguridad y Clasificación ---
    # Igual que LOCAL_DOMAINS: str CSV + @property evita el problema de
    # pydantic-settings intentando JSON-decode en campos List[str].
    NSFW_KEYWORDS: str = "porn,sex,xxx,nude,casino,gambling"
    NSFW_DOMAINS: str = "pornhub.com,xvideos.com"
    ENABLE_SAFETY_FILTER: bool = True

    # --- Pydantic V2 Config ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Propiedades derivadas (CSV str → List[str]) ---
    @property
    def local_domains_list(self) -> List[str]:
        return [x.strip().lower() for x in self.LOCAL_DOMAINS.split(",") if x.strip()]

    @property
    def nsfw_keywords_list(self) -> List[str]:
        return [x.strip().lower() for x in self.NSFW_KEYWORDS.split(",") if x.strip()]

    @property
    def nsfw_domains_list(self) -> List[str]:
        return [x.strip().lower() for x in self.NSFW_DOMAINS.split(",") if x.strip()]

    @property
    def is_production(self) -> bool:
        return getattr(self, "ENVIRONMENT", "development").lower() == "production"



@lru_cache()
def get_settings() -> Settings:
    return Settings()