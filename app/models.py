# app/models.py - VERSIÓN ACTUALIZADA CON RESILIENCIA

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, Index
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from datetime import datetime

from app.database import Base
from app.config import get_settings

settings = get_settings()


class Bookmark(Base):
    """Modelo principal de Bookmarks con búsqueda semántica y resiliencia"""
    
    __tablename__ = "bookmarks"
    
    # Identificación
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), unique=True, nullable=False, index=True)
    original_title = Column(String(512), nullable=False)
    
    # Contenido procesado
    clean_title = Column(String(512))
    summary = Column(Text)
    full_text = Column(Text)
    
    # Clasificación
    tags = Column(ARRAY(String), default=list)
    category = Column(String(100))
    
    # Safety & Privacy
    is_nsfw = Column(Boolean, default=False, index=True)
    is_local = Column(Boolean, default=False, index=True)
    nsfw_reason = Column(String(256))
    
    # ========== NUEVO: Estados de Resiliencia ==========
    
    # Estado general (mantiene compatibilidad)
    status = Column(
        String(50),
        default="pending",
        index=True,
        # Valores: pending, processing, completed, completed_partial, 
        #          failed, manual_required
    )
    error_message = Column(Text)
    
    # Estado de Scraping
    scraping_status = Column(String(50))  
    # Valores: pending, success, partial, failed, skipped
    
    scraping_strategy = Column(String(50))
    # Valores: trafilatura, trafilatura_retry, beautifulsoup, 
    #          archive_org, none
    
    scraping_error_type = Column(String(50))
    # Valores: bot_detection, timeout, connection_refused, 
    #          rate_limited, dns_error, ssl_error, unknown
    
    scraping_attempts = Column(Integer, default=0)
    # Número de intentos de scraping realizados
    
    # Estado de Curación IA
    curation_status = Column(String(50))
    # Valores: pending, success, fallback, failed
    
    curation_mode = Column(String(50))
    # Valores: full_text, url_only, enhanced_url
    
    # Métricas de Calidad
    confidence_score = Column(Float, default=0.0)
    # 0.0-1.0: Nivel de confianza en la metadata generada
    # 1.0 = scraping exitoso + curación completa
    # 0.7 = scraping exitoso + curación parcial
    # 0.5 = solo URL + título procesado con IA
    # 0.3 = fallback básico
    # 0.0 = completamente fallido
    
    # ====================================================
    
    # Embeddings (Vector Semántico)
    embedding = Column(Vector(settings.EMBEDDING_DIMENSION))
    
    # Metadata
    domain = Column(String(256), index=True)
    favicon_url = Column(String(512))
    language = Column(String(10))
    word_count = Column(Integer)
    
    # Métricas (legacy)
    relevance_score = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    scraped_at = Column(DateTime(timezone=True))
    
    # Índices para búsqueda
    __table_args__ = (
        Index('ix_bookmarks_embedding_cosine', 'embedding', postgresql_using='ivfflat'),
        Index('ix_bookmarks_tags_gin', 'tags', postgresql_using='gin'),
        Index('ix_bookmarks_category', 'category'),
        Index('ix_bookmarks_domain', 'domain'),
        Index('ix_bookmarks_created_at_desc', created_at.desc()),
        # Nuevos índices
        Index('ix_bookmarks_scraping_status', 'scraping_status'),
        Index('ix_bookmarks_confidence_score', confidence_score.desc()),
    )
    
    def __repr__(self):
        return f"<Bookmark(id={self.id}, url={self.url[:50]}, status={self.status}, confidence={self.confidence_score:.2f})>"
    
    def to_dict(self):
        """Convierte el modelo a diccionario para API"""
        return {
            "id": self.id,
            "url": self.url,
            "original_title": self.original_title,
            "clean_title": self.clean_title,
            "summary": self.summary,
            "tags": self.tags or [],
            "category": self.category,
            "is_nsfw": self.is_nsfw,
            "is_local": self.is_local,
            "status": self.status,
            "domain": self.domain,
            "language": self.language,
            "word_count": self.word_count,
            "confidence_score": self.confidence_score,
            # Nuevos campos
            "scraping_status": self.scraping_status,
            "scraping_strategy": self.scraping_strategy,
            "curation_mode": self.curation_mode,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ProcessingLog(Base):
    """Log de procesamiento para debugging y monitoreo"""
    
    __tablename__ = "processing_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    bookmark_id = Column(Integer, index=True)
    url = Column(String(2048))
    
    # Agente que procesó
    agent_name = Column(String(50), index=True)  # archivist, curator
    
    # Resultado
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    
    # Metadata de procesamiento
    processing_time = Column(Float)  # segundos
    tokens_used = Column(Integer)
    
    # ========== NUEVO: Detalles de Resiliencia ==========
    scraping_attempts = Column(Integer, default=1)
    scraping_strategy_used = Column(String(50))
    fallback_triggered = Column(Boolean, default=False)
    # ====================================================
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<ProcessingLog(id={self.id}, agent={self.agent_name}, success={self.success})>"


class SearchHistory(Base):
    """Historial de búsquedas para analytics"""
    
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(512), index=True)
    results_count = Column(Integer)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<SearchHistory(id={self.id}, query={self.query})>"