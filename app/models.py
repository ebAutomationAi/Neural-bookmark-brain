from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, Index
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from datetime import datetime

from app.database import Base
from app.config import get_settings

settings = get_settings()


class Bookmark(Base):
    """Modelo principal de Bookmarks con búsqueda semántica"""
    
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
    
    # Estado de procesamiento
    status = Column(
        String(50),
        default="pending",
        index=True,
        # Valores: pending, processing, completed, failed, manual_required
    )
    error_message = Column(Text)
    
    # Embeddings (Vector Semántico)
    embedding = Column(Vector(settings.EMBEDDING_DIMENSION))
    
    # Metadata
    domain = Column(String(256), index=True)
    favicon_url = Column(String(512))
    language = Column(String(10))
    word_count = Column(Integer)
    
    # Métricas
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
    )
    
    def __repr__(self):
        return f"<Bookmark(id={self.id}, url={self.url[:50]}, status={self.status})>"
    
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
            "relevance_score": self.relevance_score,
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
