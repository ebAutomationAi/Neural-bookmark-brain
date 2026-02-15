from pydantic import BaseModel, HttpUrl, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum


class BookmarkStatus(str, Enum):
    """Estados posibles de un bookmark"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    MANUAL_REQUIRED = "manual_required"


class BookmarkBase(BaseModel):
    """Schema base de bookmark"""
    url: str
    original_title: str


class BookmarkCreate(BaseModel):
    url: str
    original_title: Optional[str] = None
### ----------------- ###


class BookmarkUpdate(BaseModel):
    """Schema para actualizar bookmark"""
    clean_title: Optional[str] = None
    summary: Optional[str] = None
    full_text: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    is_nsfw: Optional[bool] = None
    is_local: Optional[bool] = None
    nsfw_reason: Optional[str] = None
    status: Optional[BookmarkStatus] = None
    error_message: Optional[str] = None
    embedding: Optional[List[float]] = None
    domain: Optional[str] = None
    language: Optional[str] = None
    word_count: Optional[int] = None
    relevance_score: Optional[float] = None


class BookmarkResponse(BookmarkBase):
    """Schema de respuesta de bookmark"""
    id: int
    clean_title: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = []
    category: Optional[str] = None
    is_nsfw: bool = False
    is_local: bool = False
    status: str
    domain: Optional[str] = None
    language: Optional[str] = None
    word_count: Optional[int] = None
    relevance_score: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    """Request de búsqueda semántica"""
    query: str = Field(..., min_length=1, max_length=512)
    limit: int = Field(default=10, ge=1, le=100)
    include_nsfw: bool = Field(default=False)
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    
    @validator('query')
    def validate_query(cls, v):
        """Valida que la query no esté vacía"""
        if not v.strip():
            raise ValueError("La query no puede estar vacía")
        return v.strip()


class SearchResult(BaseModel):
    """Resultado de búsqueda con score"""
    bookmark: BookmarkResponse
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    
    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    """Respuesta de búsqueda"""
    query: str
    results: List[SearchResult]
    total: int
    execution_time: float


class ImportStats(BaseModel):
    """Estadísticas de importación"""
    total_bookmarks: int
    imported: int
    duplicates: int
    failed: int
    nsfw_detected: int
    local_detected: int
    errors: List[str] = []


class ProcessingStats(BaseModel):
    """Estadísticas de procesamiento"""
    total: int
    pending: int
    processing: int
    completed: int
    failed: int
    manual_required: int
    
    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    database: str
    version: str
    timestamp: datetime
