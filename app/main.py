from fastapi import FastAPI, Depends, HTTPException, Query, status, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from typing import List, Optional
from datetime import datetime
from loguru import logger
import sys
import numpy as np  # Necesario para el fix de arrays

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.database import get_db, init_db, close_db
from app.models import Bookmark, SearchHistory, ProcessingLog
from app.schemas import (
    BookmarkResponse,
    BookmarkCreate,  # Asegúrate que esto esté en schemas.py
    SearchRequest,
    SearchResponse,
    SearchResult,
    ProcessingStats,
    HealthResponse,
)
from app.services.embeddings import get_embedding_service
from app.agents import orchestrator
from app.utils.validators import URLValidator

# Configurar logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)

settings = get_settings()

# Configurar rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_GLOBAL])

app = FastAPI(
    title="Neural Bookmark Brain",
    description="AI-Powered Semantic Knowledge Base for Bookmarks",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Añadir el limiter a la app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_cors_origins = ["*"] if settings.CORS_ORIGINS.strip() == "*" else [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Iniciando Neural Bookmark Brain...")
    try:
        await init_db()
        logger.info("✅ Base de datos inicializada")
        embedding_service = get_embedding_service()
        _ = embedding_service.model
        logger.info("✅ Modelo de embeddings cargado")
        logger.info("🎉 Sistema listo!")
    except Exception as e:
        logger.error(f"❌ Error en startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Cerrando Neural Bookmark Brain...")
    await close_db()
    logger.info("✅ Conexiones cerradas")


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "Neural Bookmark Brain",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
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


# --- Constantes de paginación y exportación ---
DEFAULT_BOOKMARK_LIMIT = 50
MAX_BOOKMARK_LIMIT = 100
MAX_EXPORT_LIMIT = 10_000


@app.post("/bookmarks", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED, tags=["Bookmarks"])
@limiter.limit(settings.RATE_LIMIT_CREATE)
async def create_bookmark(
    request: Request,
    bookmark_in: BookmarkCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):

    """
    Crea un nuevo bookmark y lo pone en cola para procesamiento
    """
    try:
        # 1. Validar URL
        is_valid, normalized_url, error_msg = URLValidator.validate_and_normalize(bookmark_in.url)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"URL inválida: {error_msg}")

        # 2. Verificar duplicados
        existing = await db.execute(select(Bookmark).where(Bookmark.url == normalized_url))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="El bookmark ya existe")

        # 3. Crear en DB
        new_bookmark = Bookmark(
            url=normalized_url,
            original_title=bookmark_in.original_title or "Pendiente de procesar",
            status="pending"
        )
        db.add(new_bookmark)
        await db.commit()
        await db.refresh(new_bookmark)

        # 4. Trigger procesamiento en background (simulado vía reprocess endpoint logic)
        # En producción real, esto iría a una cola (Celery/Redis), aquí llamamos directo
        # o dejamos que el cron/job lo recoja. Para UX inmediata, lanzamos background task.
        background_tasks.add_task(process_bookmark_background, new_bookmark.id)

        return new_bookmark
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error creando bookmark")
        raise HTTPException(status_code=500, detail="Error creando bookmark")

async def process_bookmark_background(bookmark_id: int) -> None:
    # Wrapper simple para procesar en background sin bloquear request
    # Requiere crear una nueva sesión ya que la anterior se cierra
    # NOTA: Para simplificar este fix, confiamos en el script reprocess_failed.py
    # o el endpoint /process/{id} que el usuario puede llamar.
    # Si se requiere automático, implementar aquí lógica de orchestrator con nueva sesión.
    pass


@app.post("/search", response_model=SearchResponse, tags=["Search"])
@limiter.limit(settings.RATE_LIMIT_SEARCH)
async def semantic_search(
    request: Request,
    search_request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    start_time = datetime.now()
    
    try:
        logger.info(f"🔍 Búsqueda: '{search_request.query}' (limit: {search_request.limit})")
        
        embedding_service = get_embedding_service()
        query_embedding = embedding_service.generate_query_embedding(search_request.query)
        
        query_stmt = select(Bookmark).where(Bookmark.status == "completed")
        
        if not search_request.include_nsfw:
            query_stmt = query_stmt.where(Bookmark.is_nsfw == False)
        
        if search_request.category:
            query_stmt = query_stmt.where(Bookmark.category == search_request.category)
        
        if search_request.tags:
            tag_conditions = [Bookmark.tags.contains([tag]) for tag in search_request.tags]
            query_stmt = query_stmt.where(or_(*tag_conditions))
        
        query_stmt = query_stmt.order_by(
            Bookmark.embedding.cosine_distance(query_embedding)
        ).limit(search_request.limit)
        
        result = await db.execute(query_stmt)
        bookmarks = result.scalars().all()
        
        search_results = []
        for bookmark in bookmarks:
            ### FIX: Comprobación segura de arrays NumPy/Listas ###
            has_embedding = False
            if bookmark.embedding is not None:
                if isinstance(bookmark.embedding, (list, np.ndarray)):
                    has_embedding = len(bookmark.embedding) > 0
                else:
                    has_embedding = True # Fallback

            if has_embedding:
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
        
        search_history = SearchHistory(
            query=search_request.query,
            results_count=len(search_results)
        )
        db.add(search_history)
        await db.commit()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return SearchResponse(
            query=search_request.query,
            results=search_results,
            total=len(search_results),
            execution_time=execution_time
        )
    
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error en búsqueda")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en búsqueda",
        )


@app.get("/bookmarks/{bookmark_id}", response_model=BookmarkResponse, tags=["Bookmarks"])
async def get_bookmark(bookmark_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Bookmark).where(Bookmark.id == bookmark_id))
        bookmark = result.scalar_one_or_none()
        if not bookmark:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark no encontrado")
        return BookmarkResponse.from_orm(bookmark)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error obteniendo bookmark")
        raise HTTPException(status_code=500, detail="Error obteniendo bookmark")


@app.get("/bookmarks", response_model=List[BookmarkResponse], tags=["Bookmarks"])
async def list_bookmarks(
    skip: int = Query(0, ge=0),
    limit: int = Query(DEFAULT_BOOKMARK_LIMIT, ge=1, le=MAX_BOOKMARK_LIMIT),
    status_filter: Optional[str] = None,
    category: Optional[str] = None,
    include_nsfw: bool = False,
    db: AsyncSession = Depends(get_db)
):
    try:
        query = select(Bookmark)
        if status_filter:
            query = query.where(Bookmark.status == status_filter)
        if category:
            query = query.where(Bookmark.category == category)
        if not include_nsfw:
            query = query.where(Bookmark.is_nsfw == False)
        
        query = query.order_by(Bookmark.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        bookmarks = result.scalars().all()
        return [BookmarkResponse.from_orm(b) for b in bookmarks]
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error listando bookmarks")
        raise HTTPException(status_code=500, detail="Error listando bookmarks")


@app.get("/stats/processing", response_model=ProcessingStats, tags=["Statistics"])
async def get_processing_stats(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Bookmark.status, func.count(Bookmark.id).label('count')).group_by(Bookmark.status))
        stats_by_status = {row.status: row.count for row in result}
        total_result = await db.execute(select(func.count(Bookmark.id)))
        total = total_result.scalar()
        
        return ProcessingStats(
            total=total,
            pending=stats_by_status.get('pending', 0),
            processing=stats_by_status.get('processing', 0),
            completed=stats_by_status.get('completed', 0),
            failed=stats_by_status.get('failed', 0),
            manual_required=stats_by_status.get('manual_required', 0),
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error obteniendo estadísticas de procesamiento")
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas")


@app.get("/stats/categories", tags=["Statistics"])
async def get_category_stats(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(Bookmark.category, func.count(Bookmark.id).label('count'))
            .where(and_(Bookmark.category.isnot(None), Bookmark.status == "completed"))
            .group_by(Bookmark.category).order_by(func.count(Bookmark.id).desc())
        )
        categories = [{"category": row.category, "count": row.count} for row in result]
        return {"categories": categories}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error obteniendo estadísticas de categorías")
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas de categorías")


@app.get("/stats/tags", tags=["Statistics"])
async def get_tag_stats(limit: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            text("SELECT unnest(tags) as tag, COUNT(*) as count FROM bookmarks WHERE status = 'completed' AND tags IS NOT NULL GROUP BY tag ORDER BY count DESC LIMIT :limit"),
            {"limit": limit}
        )
        tags = [{"tag": row.tag, "count": row.count} for row in result]
        return {"tags": tags}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error obteniendo estadísticas de tags")
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas de tags")

@app.get("/export/json")
async def export_json(
    limit: int = Query(MAX_EXPORT_LIMIT, ge=1, le=MAX_EXPORT_LIMIT),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(select(Bookmark).order_by(Bookmark.created_at.desc()).limit(limit))
        bookmarks = result.scalars().all()
        data = [b.to_dict() for b in bookmarks]
        return JSONResponse(content=data)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error exportando a JSON")
        raise HTTPException(status_code=500, detail="Error exportando a JSON")

@app.get("/export/markdown")
async def export_markdown(
    limit: int = Query(MAX_EXPORT_LIMIT, ge=1, le=MAX_EXPORT_LIMIT),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(select(Bookmark).order_by(Bookmark.created_at.desc()).limit(limit))
        bookmarks = result.scalars().all()
        md = "# My Bookmarks\n\n"
        for b in bookmarks:
            title = b.clean_title or b.original_title or "Sin título"
            tags_str = ", ".join(b.tags) if b.tags else ""
            md += f"## {title}\n"
            md += f"- **URL**: {b.url}\n"
            md += f"- **Category**: {b.category}\n"
            md += f"- **Tags**: {tags_str}\n\n"
            md += f"{b.summary or ''}\n\n---\n\n"
        return Response(content=md, media_type="text/markdown")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error exportando a Markdown")
        raise HTTPException(status_code=500, detail="Error exportando a Markdown")


@app.post("/process/{bookmark_id}", tags=["Processing"])
@limiter.limit(settings.RATE_LIMIT_CREATE)
async def reprocess_bookmark(request: Request, bookmark_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Bookmark).where(Bookmark.id == bookmark_id))
    bookmark = result.scalar_one_or_none()
    
    if not bookmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark no encontrado")
    
    try:
        bookmark.status = "processing"
        await db.commit()
        
        result = await orchestrator.process_bookmark(bookmark.url, bookmark.original_title)
        
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
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error re-procesando bookmark %s", bookmark_id)
        bookmark.status = "failed"
        bookmark.error_message = str(e)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error procesando")

@app.post("/admin/reembed-all")
async def reembed_all_bookmarks(db: AsyncSession = Depends(get_db)):
    """Re-genera embeddings para todos los bookmarks"""
    try:
        bookmarks = await db.execute(
            select(Bookmark).where(Bookmark.status == "completed")
        )
        
        embedding_service = get_embedding_service()
        count = 0
        for bookmark in bookmarks.scalars():
            try:
                text = f"{bookmark.clean_title}. {bookmark.summary}"
                bookmark.embedding = embedding_service.generate_embedding(text)
                count += 1
            except Exception:
                logger.exception("Error generando embedding para bookmark %s", bookmark.id)
        await db.commit()
        return {"status": "success", "count": count}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error en reembed-all")
        raise HTTPException(status_code=500, detail="Error regenerando embeddings")


@app.post("/search/hybrid")
async def hybrid_search(query: str, db: AsyncSession = Depends(get_db)):
    try:
        # Búsqueda semántica
        embedding_service = get_embedding_service()
        embedding = embedding_service.generate_query_embedding(query)
        semantic_results = await db.execute(
            select(Bookmark)
            .order_by(Bookmark.embedding.cosine_distance(embedding))
            .limit(20)
        )
        
        # Búsqueda por keywords en título/tags
        keyword_results = await db.execute(
            select(Bookmark)
            .where(
                or_(
                    Bookmark.clean_title.ilike(f"%{query}%"),
                    Bookmark.tags.contains([query.lower()])
                )
            )
            .limit(20)
        )
        
        return {
            "semantic": [BookmarkResponse.from_orm(b) for b in semantic_results.scalars()],
            "keyword": [BookmarkResponse.from_orm(b) for b in keyword_results.scalars()]
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error en búsqueda híbrida")
        raise HTTPException(status_code=500, detail="Error en búsqueda híbrida")
    

@app.delete("/bookmarks/{bookmark_id}", tags=["Bookmarks"])
async def delete_bookmark(bookmark_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Bookmark).where(Bookmark.id == bookmark_id))
        bookmark = result.scalar_one_or_none()
        
        if not bookmark:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark no encontrado")
        
        await db.delete(bookmark)
        await db.commit()
        return {"success": True, "message": "Bookmark eliminado"}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error eliminando bookmark")
        raise HTTPException(status_code=500, detail="Error eliminando bookmark")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)