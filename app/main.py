from fastapi import FastAPI, Depends, HTTPException, Query, status, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
@app.post("/import/csv", response_model=ImportJobResponse)
async def import_csv_upload(
    file: UploadFile = File(...),
    batch_size: int = Query(10, ge=1, le=50),
    background_tasks: BackgroundTasks
):
    """
    Importar CSV desde UI
    - Sube archivo
    - Valida formato
    - Encola procesamiento async
    - Retorna job_id para tracking
    """
    # 1. Validar CSV
    # 2. Guardar en /tmp
    # 3. Crear ImportJob en DB
    # 4. Encolar en background
    # 5. Retornar job_id

@app.get("/import/status/{job_id}")
async def import_status(job_id: str):
c
    Tracking de importación en tiempo real
    Output: {
        job_id, status, 
        total, processed, failed,
        progress_percent,
        eta_seconds
    }
@app.post("/import/csv", response_model=ImportJobResponse)
async def import_csv_upload(
    file: UploadFile = File(...),
    batch_size: int = Query(10, ge=1, le=50),
    background_tasks: BackgroundTasks
):
    """
    Importar CSV desde UI
    - Sube archivo
    - Valida formato
    - Encola procesamiento async
    - Retorna job_id para tracking
    """
    # 1. Validar CSV
    # 2. Guardar en /tmp
    # 3. Crear ImportJob en DB
    # 4. Encolar en background
    # 5. Retornar job_id

@app.get("/import/status/{job_id}")
async def import_status(job_id: str):
    """
    Tracking de importación en tiempo real
    Output: {
        job_id, status, 
        total, processed, failed,
        progress_percent,
        eta_seconds
    }
    """
    # 1. Consultar ImportJob por job_id
    # 2. Retornar status y progreso
    pass

### NEW: Endpoint para crear bookmarks ###
@app.post("/bookmarks", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED, tags=["Bookmarks"])
@limiter.limit(settings.RATE_LIMIT_CREATE)
async def create_bookmark(
    req: Request,
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
        print(f"Error creando bookmark: {e}")
        logger.error(f"Error creando bookmark: {e}")
        raise HTTPException(status_code=500, detail=f"Error creando bookmark: {str(e)}")

async def process_bookmark_background(bookmark_id: int):
    # Wrapper simple para procesar en background sin bloquear request
    # Requiere crear una nueva sesión ya que la anterior se cierra
    # NOTA: Para simplificar este fix, confiamos en el script reprocess_failed.py
    # o el endpoint /process/{id} que el usuario puede llamar.
    # Si se requiere automático, implementar aquí lógica de orchestrator con nueva sesión.
    pass


@app.post("/search", response_model=SearchResponse, tags=["Search"])
@limiter.limit(settings.RATE_LIMIT_SEARCH)
async def semantic_search(
    req: Request,
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    start_time = datetime.now()
    
    try:
        logger.info(f"🔍 Búsqueda: '{request.query}' (limit: {request.limit})")
        
        embedding_service = get_embedding_service()
        query_embedding = embedding_service.generate_query_embedding(request.query)
        
        query_stmt = select(Bookmark).where(Bookmark.status == "completed")
        
        if not request.include_nsfw:
            query_stmt = query_stmt.where(Bookmark.is_nsfw == False)
        
        if request.category:
            query_stmt = query_stmt.where(Bookmark.category == request.category)
        
        if request.tags:
            tag_conditions = [Bookmark.tags.contains([tag]) for tag in request.tags]
            query_stmt = query_stmt.where(or_(*tag_conditions))
        
        query_stmt = query_stmt.order_by(
            Bookmark.embedding.cosine_distance(query_embedding)
        ).limit(request.limit)
        
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
            query=request.query,
            results_count=len(search_results)
        )
        db.add(search_history)
        await db.commit()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return SearchResponse(
            query=request.query,
            results=search_results,
            total=len(search_results),
            execution_time=execution_time
        )
    
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        # Log completo para debug
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en búsqueda: {str(e)}"
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
    except Exception as e:
        print(f"Error obteniendo bookmark: {e}")
        logger.error(f"Error obteniendo bookmark: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo bookmark: {str(e)}")


@app.get("/bookmarks", response_model=List[BookmarkResponse], tags=["Bookmarks"])
async def list_bookmarks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
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
    except Exception as e:
        print(f"Error listando bookmarks: {e}")
        logger.error(f"Error listando bookmarks: {e}")
        raise HTTPException(status_code=500, detail=f"Error listando bookmarks: {str(e)}")


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
    except Exception as e:
        print(f"Error obteniendo estadísticas de procesamiento: {e}")
        logger.error(f"Error obteniendo estadísticas de procesamiento: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")


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
    except Exception as e:
        print(f"Error obteniendo estadísticas de categorías: {e}")
        logger.error(f"Error obteniendo estadísticas de categorías: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas de categorías: {str(e)}")


@app.get("/stats/tags", tags=["Statistics"])
async def get_tag_stats(limit: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            text("SELECT unnest(tags) as tag, COUNT(*) as count FROM bookmarks WHERE status = 'completed' AND tags IS NOT NULL GROUP BY tag ORDER BY count DESC LIMIT :limit"),
            {"limit": limit}
        )
        tags = [{"tag": row.tag, "count": row.count} for row in result]
        return {"tags": tags}
    except Exception as e:
        print(f"Error obteniendo estadísticas de tags: {e}")
        logger.error(f"Error obteniendo estadísticas de tags: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas de tags: {str(e)}")

@app.get("/export/json")
async def export_json(db: AsyncSession = Depends(get_db)):
    try:
        bookmarks = await db.execute(select(Bookmark))
        data = [b.to_dict() for b in bookmarks.scalars()]
        return JSONResponse(content=data)
    except Exception as e:
        print(f"Error exportando a JSON: {e}")
        logger.error(f"Error exportando a JSON: {e}")
        raise HTTPException(status_code=500, detail=f"Error exportando a JSON: {str(e)}")

@app.get("/export/markdown")
async def export_markdown(db: AsyncSession = Depends(get_db)):
    try:
        bookmarks = await db.execute(select(Bookmark))
        md = "# My Bookmarks\n\n"
        for b in bookmarks.scalars():
            md += f"## {b.clean_title}\n"
            md += f"- **URL**: {b.url}\n"
            md += f"- **Category**: {b.category}\n"
            md += f"- **Tags**: {', '.join(b.tags)}\n\n"
            md += f"{b.summary}\n\n---\n\n"
        
        return Response(content=md, media_type="text/markdown")
    except Exception as e:
        print(f"Error exportando a Markdown: {e}")
        logger.error(f"Error exportando a Markdown: {e}")
        raise HTTPException(status_code=500, detail=f"Error exportando a Markdown: {str(e)}")


@app.post("/process/{bookmark_id}", tags=["Processing"])
@limiter.limit(settings.RATE_LIMIT_CREATE)
async def reprocess_bookmark(req: Request, bookmark_id: int, db: AsyncSession = Depends(get_db)):
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
    
    except Exception as e:
        logger.error(f"Error re-procesando bookmark {bookmark_id}: {e}")
        bookmark.status = "failed"
        bookmark.error_message = str(e)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error procesando: {str(e)}")

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
            except Exception as e:
                print(f"Error generando embedding para bookmark {bookmark.id}: {e}")
                logger.error(f"Error generando embedding para bookmark {bookmark.id}: {e}")
        
        await db.commit()
        return {"status": "success", "count": count}
    except Exception as e:
        print(f"Error en reembed-all: {e}")
        logger.error(f"Error en reembed-all: {e}")
        raise HTTPException(status_code=500, detail=f"Error regenerando embeddings: {str(e)}")

    # Combinar full-text search con vectores
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
    except Exception as e:
        print(f"Error en búsqueda híbrida: {e}")
        logger.error(f"Error en búsqueda híbrida: {e}")
        raise HTTPException(status_code=500, detail=f"Error en búsqueda híbrida: {str(e)}")
    

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
    except Exception as e:
        print(f"Error eliminando bookmark: {e}")
        logger.error(f"Error eliminando bookmark: {e}")
        raise HTTPException(status_code=500, detail=f"Error eliminando bookmark: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

    @app.get("/settings", response_model=UserSettings)
async def get_settings():
    """Leer configuración actual"""

@app.put("/settings")
async def update_settings(settings: UserSettingsUpdate):
    """
    Actualizar settings:
    - Groq API key
    - Embedding model
    - NSFW keywords
    - Default filters
    """