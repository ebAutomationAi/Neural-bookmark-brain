from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from typing import List, Optional
from datetime import datetime
from loguru import logger
import sys

from app.config import get_settings
from app.database import get_db, init_db, close_db
from app.models import Bookmark, SearchHistory, ProcessingLog
from app.schemas import (
    BookmarkResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    ProcessingStats,
    HealthResponse,
)
from app.services.embeddings import get_embedding_service
from app.agents import orchestrator

# Configurar logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)

settings = get_settings()

# Crear aplicación
app = FastAPI(
    title="Neural Bookmark Brain",
    description="AI-Powered Semantic Knowledge Base for Bookmarks",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Inicialización al arrancar"""
    logger.info("🚀 Iniciando Neural Bookmark Brain...")
    
    try:
        # Inicializar base de datos
        await init_db()
        logger.info("✅ Base de datos inicializada")
        
        # Cargar modelo de embeddings
        embedding_service = get_embedding_service()
        _ = embedding_service.model  # Trigger lazy loading
        logger.info("✅ Modelo de embeddings cargado")
        
        logger.info("🎉 Sistema listo!")
        
    except Exception as e:
        logger.error(f"❌ Error en startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al apagar"""
    logger.info("👋 Cerrando Neural Bookmark Brain...")
    await close_db()
    logger.info("✅ Conexiones cerradas")


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz"""
    return {
        "service": "Neural Bookmark Brain",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check del sistema"""
    try:
        # Verificar conexión a DB
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        database=db_status,
        version="1.0.0",
        timestamp=datetime.now()
    )


@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def semantic_search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Búsqueda semántica de bookmarks usando embeddings
    
    - **query**: Texto de búsqueda
    - **limit**: Número máximo de resultados (1-100)
    - **include_nsfw**: Incluir contenido NSFW (default: False)
    - **category**: Filtrar por categoría
    - **tags**: Filtrar por tags
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"🔍 Búsqueda: '{request.query}' (limit: {request.limit})")
        
        # Generar embedding de la query
        embedding_service = get_embedding_service()
        query_embedding = embedding_service.generate_query_embedding(request.query)
        
        # Construir query base
        query_stmt = select(Bookmark).where(
            Bookmark.status == "completed"
        )
        
        # Filtro NSFW
        if not request.include_nsfw:
            query_stmt = query_stmt.where(Bookmark.is_nsfw == False)
        
        # Filtro de categoría
        if request.category:
            query_stmt = query_stmt.where(Bookmark.category == request.category)
        
        # Filtro de tags
        if request.tags:
            # Buscar bookmarks que contengan al menos uno de los tags
            tag_conditions = [
                Bookmark.tags.contains([tag]) for tag in request.tags
            ]
            query_stmt = query_stmt.where(or_(*tag_conditions))
        
        # Ordenar por similitud coseno (usando operador <=> de pgvector)
        query_stmt = query_stmt.order_by(
            Bookmark.embedding.cosine_distance(query_embedding)
        ).limit(request.limit)
        
        # Ejecutar query
        result = await db.execute(query_stmt)
        bookmarks = result.scalars().all()
        
        # Calcular similarity scores
        search_results = []
        for bookmark in bookmarks:
            # Calcular similitud
            if bookmark.embedding:
                similarity = embedding_service.calculate_similarity(
                    query_embedding,
                    bookmark.embedding
                )
            else:
                similarity = 0.0
            
            search_results.append(
                SearchResult(
                    bookmark=BookmarkResponse.from_orm(bookmark),
                    similarity_score=similarity
                )
            )
        
        # Guardar búsqueda en historial
        search_history = SearchHistory(
            query=request.query,
            results_count=len(search_results)
        )
        db.add(search_history)
        await db.commit()
        
        # Calcular tiempo de ejecución
        execution_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(
            f"✅ Búsqueda completada: {len(search_results)} resultados "
            f"en {execution_time:.3f}s"
        )
        
        return SearchResponse(
            query=request.query,
            results=search_results,
            total=len(search_results),
            execution_time=execution_time
        )
    
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en búsqueda: {str(e)}"
        )


@app.get("/bookmarks/{bookmark_id}", response_model=BookmarkResponse, tags=["Bookmarks"])
async def get_bookmark(
    bookmark_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Obtiene un bookmark por ID"""
    result = await db.execute(
        select(Bookmark).where(Bookmark.id == bookmark_id)
    )
    bookmark = result.scalar_one_or_none()
    
    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark no encontrado"
        )
    
    return BookmarkResponse.from_orm(bookmark)


@app.get("/bookmarks", response_model=List[BookmarkResponse], tags=["Bookmarks"])
async def list_bookmarks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = None,
    category: Optional[str] = None,
    include_nsfw: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista bookmarks con paginación
    
    - **skip**: Número de registros a saltar
    - **limit**: Número máximo de registros
    - **status_filter**: Filtrar por estado (pending, completed, failed, etc.)
    - **category**: Filtrar por categoría
    - **include_nsfw**: Incluir contenido NSFW
    """
    query = select(Bookmark)
    
    # Filtros
    if status_filter:
        query = query.where(Bookmark.status == status_filter)
    
    if category:
        query = query.where(Bookmark.category == category)
    
    if not include_nsfw:
        query = query.where(Bookmark.is_nsfw == False)
    
    # Ordenar por fecha de creación (más recientes primero)
    query = query.order_by(Bookmark.created_at.desc())
    
    # Paginación
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    bookmarks = result.scalars().all()
    
    return [BookmarkResponse.from_orm(b) for b in bookmarks]


@app.get("/stats/processing", response_model=ProcessingStats, tags=["Statistics"])
async def get_processing_stats(db: AsyncSession = Depends(get_db)):
    """Obtiene estadísticas de procesamiento"""
    
    # Contar por estado
    result = await db.execute(
        select(
            Bookmark.status,
            func.count(Bookmark.id).label('count')
        ).group_by(Bookmark.status)
    )
    
    stats_by_status = {row.status: row.count for row in result}
    
    # Contar total
    total_result = await db.execute(
        select(func.count(Bookmark.id))
    )
    total = total_result.scalar()
    
    return ProcessingStats(
        total=total,
        pending=stats_by_status.get('pending', 0),
        processing=stats_by_status.get('processing', 0),
        completed=stats_by_status.get('completed', 0),
        failed=stats_by_status.get('failed', 0),
        manual_required=stats_by_status.get('manual_required', 0),
    )


@app.get("/stats/categories", tags=["Statistics"])
async def get_category_stats(db: AsyncSession = Depends(get_db)):
    """Estadísticas por categoría"""
    result = await db.execute(
        select(
            Bookmark.category,
            func.count(Bookmark.id).label('count')
        ).where(
            and_(
                Bookmark.category.isnot(None),
                Bookmark.status == "completed"
            )
        ).group_by(Bookmark.category).order_by(func.count(Bookmark.id).desc())
    )
    
    categories = [
        {"category": row.category, "count": row.count}
        for row in result
    ]
    
    return {"categories": categories}


@app.get("/stats/tags", tags=["Statistics"])
async def get_tag_stats(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Top tags más usados"""
    # Usar unnest para expandir el array de tags
    result = await db.execute(
        text("""
            SELECT unnest(tags) as tag, COUNT(*) as count
            FROM bookmarks
            WHERE status = 'completed' AND tags IS NOT NULL
            GROUP BY tag
            ORDER BY count DESC
            LIMIT :limit
        """),
        {"limit": limit}
    )
    
    tags = [
        {"tag": row.tag, "count": row.count}
        for row in result
    ]
    
    return {"tags": tags}


@app.post("/process/{bookmark_id}", tags=["Processing"])
async def reprocess_bookmark(
    bookmark_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Re-procesa un bookmark manualmente"""
    # Obtener bookmark
    result = await db.execute(
        select(Bookmark).where(Bookmark.id == bookmark_id)
    )
    bookmark = result.scalar_one_or_none()
    
    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark no encontrado"
        )
    
    try:
        # Marcar como procesando
        bookmark.status = "processing"
        await db.commit()
        
        # Procesar con agentes
        result = await orchestrator.process_bookmark(
            bookmark.url,
            bookmark.original_title
        )
        
        # Actualizar bookmark con resultados
        bookmark.clean_title = result.get("clean_title")
        bookmark.summary = result.get("summary")
        bookmark.full_text = result.get("full_text")
        bookmark.tags = result.get("tags", [])
        bookmark.category = result.get("category")
        bookmark.is_nsfw = result.get("is_nsfw", False)
        bookmark.nsfw_reason = result.get("nsfw_reason")
        bookmark.is_local = result.get("is_local", False)
        bookmark.domain = result.get("domain")
        bookmark.language = result.get("language")
        bookmark.word_count = result.get("word_count", 0)
        bookmark.embedding = result.get("embedding")
        bookmark.status = result.get("status", "failed")
        bookmark.error_message = result.get("error")
        
        await db.commit()
        
        # Log de procesamiento
        log = ProcessingLog(
            bookmark_id=bookmark.id,
            url=bookmark.url,
            agent_name="orchestrator",
            success=result.get("success", False),
            error_message=result.get("error"),
            processing_time=result.get("processing_time", 0)
        )
        db.add(log)
        await db.commit()
        
        return {
            "success": True,
            "bookmark_id": bookmark.id,
            "status": bookmark.status,
            "processing_time": result.get("processing_time", 0)
        }
    
    except Exception as e:
        logger.error(f"Error re-procesando bookmark {bookmark_id}: {e}")
        bookmark.status = "failed"
        bookmark.error_message = str(e)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando: {str(e)}"
        )


@app.delete("/bookmarks/{bookmark_id}", tags=["Bookmarks"])
async def delete_bookmark(
    bookmark_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Elimina un bookmark"""
    result = await db.execute(
        select(Bookmark).where(Bookmark.id == bookmark_id)
    )
    bookmark = result.scalar_one_or_none()
    
    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark no encontrado"
        )
    
    await db.delete(bookmark)
    await db.commit()
    
    return {"success": True, "message": "Bookmark eliminado"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
