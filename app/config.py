from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración centralizada de la aplicación"""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://bookmark_user:bookmark_pass_2024@localhost:5432/neural_bookmarks"
    
    # AI Configuration
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.1-70b-versatile"
    GROQ_TEMPERATURE: float = 0.3
    GROQ_MAX_TOKENS: int = 2048
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # Application Settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    MAX_CONCURRENT_REQUESTS: int = 10
    
    # Scraping Configuration
    SCRAPER_TIMEOUT: int = 30
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (compatible; NeuralBookmarkBot/1.0)"
    SCRAPER_MAX_RETRIES: int = 3
    
    # Safety Configuration
    NSFW_KEYWORDS: str = "adult,porn,xxx,sex,nude,nsfw,18+,onlyfans,escort"
    NSFW_DOMAINS: str = "pornhub.com,xvideos.com,xnxx.com,redtube.com,onlyfans.com"
    
    # Local Development Domains
    LOCAL_DOMAINS: str = ".local,.test,localhost,127.0.0.1,192.168"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def nsfw_keywords_list(self) -> List[str]:
        """Convierte NSFW_KEYWORDS en lista"""
        return [kw.strip().lower() for kw in self.NSFW_KEYWORDS.split(",")]
    
    @property
    def nsfw_domains_list(self) -> List[str]:
        """Convierte NSFW_DOMAINS en lista"""
        return [domain.strip().lower() for domain in self.NSFW_DOMAINS.split(",")]
    
    @property
    def local_domains_list(self) -> List[str]:
        """Convierte LOCAL_DOMAINS en lista"""
        return [domain.strip().lower() for domain in self.LOCAL_DOMAINS.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Verifica si estamos en producción"""
        return self.ENVIRONMENT.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """Singleton de configuración"""
    return Settings()
