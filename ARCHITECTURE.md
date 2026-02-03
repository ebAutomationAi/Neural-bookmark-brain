# 🏗️ Arquitectura Técnica - Neural Bookmark Brain

## Visión General

Neural Bookmark Brain es un sistema de **Knowledge Base Semántico** que utiliza **Dual AI Agents** para transformar bookmarks caóticos en una base de datos estructurada, categorizada y semánticamente buscable.

---

## Stack Tecnológico

### Backend
- **FastAPI** 0.109.0 - Framework web asíncrono
- **Python** 3.11+ - Lenguaje principal
- **SQLAlchemy** 2.0.25 - ORM asíncrono
- **asyncpg** - Driver PostgreSQL asíncrono

### Base de Datos
- **PostgreSQL** 16 - Base de datos relacional
- **pgvector** - Extensión para vector similarity search
- **Vector Embeddings** - 384/768 dimensiones (configurable)

### AI & ML
- **Groq API** - LLM inference (Llama 3.1 70B)
- **Sentence Transformers** - Embeddings semánticos
- **Trafilatura** - Web content extraction

### Infrastructure
- **Docker** + **Docker Compose** - Containerización
- **Uvicorn** - ASGI server

---

## Arquitectura de Componentes

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                         │
│  - HTTP Clients (curl, requests, browser)               │
│  - Swagger UI / ReDoc                                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  API LAYER (FastAPI)                    │
│                                                         │
│  Endpoints:                                             │
│  ├─ POST   /search          (Semantic Search)          │
│  ├─ GET    /bookmarks       (List/Filter)              │
│  ├─ GET    /bookmarks/{id}  (Get One)                  │
│  ├─ POST   /process/{id}    (Reprocess)                │
│  ├─ DELETE /bookmarks/{id}  (Delete)                   │
│  ├─ GET    /stats/*         (Analytics)                │
│  └─ GET    /health          (Health Check)             │
│                                                         │
│  Middleware:                                            │
│  ├─ CORS                                                │
│  ├─ Error Handling                                      │
│  └─ Request Logging                                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              ORCHESTRATOR LAYER                         │
│                                                         │
│  AgentOrchestrator                                      │
│  ├─ Coordina flujo entre agentes                       │
│  ├─ Gestiona errores y reintentos                      │
│  ├─ Registra métricas de procesamiento                 │
│  └─ Control de estado (pending → processing → done)    │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌──────────────────┐    ┌──────────────────────┐
│   AGENT 1        │    │     AGENT 2          │
│   ARCHIVIST      │───▶│     CURATOR          │
│  (Gatekeeper)    │    │    (Librarian)       │
│                  │    │                      │
│ Responsabilidades│    │  Responsabilidades   │
│ ├─ URL Validation│    │  ├─ AI Summary (3)   │
│ ├─ Web Scraping  │    │  ├─ Tag Generation   │
│ ├─ NSFW Detection│    │  ├─ Categorization   │
│ ├─ Title Cleaning│    │  └─ Embeddings       │
│ └─ Local Check   │    │                      │
└──────────────────┘    └──────────────────────┘
        │                         │
        └────────────┬────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│              SERVICE LAYER                              │
│                                                         │
│  ContentScraper (Trafilatura)                           │
│  ├─ HTTP client (httpx)                                 │
│  ├─ Content extraction                                  │
│  └─ Metadata parsing                                    │
│                                                         │
│  SafetyClassifier                                       │
│  ├─ Keyword matching                                    │
│  ├─ Domain blacklist                                    │
│  └─ Threshold scoring                                   │
│                                                         │
│  EmbeddingService                                       │
│  ├─ SentenceTransformer model                           │
│  ├─ Batch processing                                    │
│  └─ Vector normalization                                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              DATA LAYER (SQLAlchemy)                    │
│                                                         │
│  Models:                                                │
│  ├─ Bookmark        (main table)                        │
│  ├─ ProcessingLog   (audit trail)                      │
│  └─ SearchHistory   (analytics)                         │
│                                                         │
│  Connection Pool:                                       │
│  ├─ Async Engine (asyncpg)                              │
│  ├─ Pool size: 10                                       │
│  └─ Max overflow: 20                                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           DATABASE (PostgreSQL + pgvector)              │
│                                                         │
│  Tables:                                                │
│  ├─ bookmarks                                           │
│  │  ├─ id (PK)                                          │
│  │  ├─ url (unique)                                     │
│  │  ├─ original_title                                   │
│  │  ├─ clean_title                                      │
│  │  ├─ summary                                          │
│  │  ├─ full_text                                        │
│  │  ├─ tags (array)                                     │
│  │  ├─ category                                         │
│  │  ├─ embedding (vector[384])  ← pgvector              │
│  │  ├─ is_nsfw, is_local                                │
│  │  └─ status, timestamps                               │
│  │                                                      │
│  ├─ processing_logs                                     │
│  └─ search_history                                      │
│                                                         │
│  Indexes:                                               │
│  ├─ embedding (IVFFlat for similarity)                  │
│  ├─ tags (GIN for array search)                         │
│  ├─ created_at, domain, category                        │
│  └─ unique(url)                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Flujo de Datos

### 1. Importación (CSV → Database)

```
CSV File
   │
   ▼
[import_csv.py]
   │
   ├─ Parse CSV (pandas)
   ├─ Validate URLs
   ├─ Check duplicates
   ├─ Create Bookmark (status: pending)
   │
   ▼
[Orchestrator.process_bookmark()]
   │
   ├──▶ [Archivist Agent]
   │      ├─ Scrape URL
   │      ├─ Extract text
   │      ├─ NSFW check
   │      ├─ Clean title
   │      └─ Return: {text, title, domain, ...}
   │
   └──▶ [Curator Agent]
          ├─ Generate summary (AI)
          ├─ Generate tags (AI)
          ├─ Assign category (AI)
          ├─ Create embedding (ML)
          └─ Return: {summary, tags, category, embedding}
   │
   ▼
[Database Update]
   ├─ Update bookmark
   ├─ Set status: completed
   ├─ Create processing log
   └─ Commit transaction
```

### 2. Búsqueda Semántica (Query → Results)

```
User Query: "machine learning tutorials"
   │
   ▼
[POST /search endpoint]
   │
   ├─ Generate query embedding
   │     └─ EmbeddingService.generate_query_embedding()
   │
   ├─ Build SQL query
   │     ├─ WHERE status = 'completed'
   │     ├─ WHERE is_nsfw = false (if filter enabled)
   │     ├─ WHERE category = X (if specified)
   │     └─ ORDER BY embedding <=> query_vector
   │           └─ pgvector cosine distance operator
   │
   ├─ Execute query
   │     └─ Returns top K most similar bookmarks
   │
   ├─ Calculate similarity scores
   │     └─ Cosine similarity for each result
   │
   └─ Return SearchResponse
         └─ {results: [{bookmark, score}, ...], total, time}
```

---

## Modelo de Datos

### Bookmark Table Schema

```sql
CREATE TABLE bookmarks (
    id SERIAL PRIMARY KEY,
    url VARCHAR(2048) UNIQUE NOT NULL,
    original_title VARCHAR(512) NOT NULL,
    clean_title VARCHAR(512),
    summary TEXT,
    full_text TEXT,
    
    -- Clasificación
    tags VARCHAR[] DEFAULT '{}',
    category VARCHAR(100),
    
    -- Safety
    is_nsfw BOOLEAN DEFAULT FALSE,
    is_local BOOLEAN DEFAULT FALSE,
    nsfw_reason VARCHAR(256),
    
    -- Estado
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    
    -- Vector semántico
    embedding vector(384),  -- pgvector type
    
    -- Metadata
    domain VARCHAR(256),
    favicon_url VARCHAR(512),
    language VARCHAR(10),
    word_count INTEGER,
    relevance_score FLOAT DEFAULT 0.0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    scraped_at TIMESTAMP WITH TIME ZONE
);

-- Índices
CREATE INDEX idx_embedding_cosine ON bookmarks 
    USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_tags_gin ON bookmarks USING gin(tags);
CREATE INDEX idx_status ON bookmarks(status);
CREATE INDEX idx_is_nsfw ON bookmarks(is_nsfw);
CREATE INDEX idx_category ON bookmarks(category);
CREATE INDEX idx_created_desc ON bookmarks(created_at DESC);
```

---

## Algoritmo de Búsqueda Semántica

### Cosine Similarity con pgvector

```python
# 1. Usuario hace query
query = "machine learning frameworks"

# 2. Generar embedding de la query
query_embedding = embedding_service.generate_embedding(query)
# → [0.123, -0.456, 0.789, ..., 0.234]  (384 dimensiones)

# 3. Búsqueda en base de datos
sql = """
SELECT *,
       1 - (embedding <=> :query_vector) AS similarity
FROM bookmarks
WHERE status = 'completed'
  AND is_nsfw = false
ORDER BY embedding <=> :query_vector
LIMIT 10;
"""

# 4. pgvector calcula cosine distance
# <=> operator usa índice IVFFlat para búsqueda rápida
# Complejidad: O(log n) en lugar de O(n)

# 5. Convertir distance a similarity
similarity = 1 - cosine_distance
# similarity ∈ [0, 1] donde 1 = idéntico, 0 = opuesto
```

### IVFFlat Index

```
Vector Space (384 dimensions)
     │
     ├─ Clustering (K-means)
     │     └─ Divide space en centroides
     │
     ├─ Indexing
     │     └─ Asigna vectores a clusters
     │
     └─ Search
           ├─ 1. Encuentra cluster más cercano
           ├─ 2. Busca solo en ese cluster
           └─ 3. Retorna top K resultados
           
Ventaja: 10-100x más rápido que brute force
Trade-off: ~95% accuracy vs 100% exactitud
```

---

## Agente Architecture Pattern

### Archivist Agent (Content Acquisition)

```python
class ArchivistAgent:
    async def process(url, title) -> Dict:
        # 1. Scraping
        content = await scraper.scrape_url(url)
        
        # 2. Safety Classification
        is_nsfw, reason = classifier.classify(
            url, title, content['text']
        )
        
        # 3. Title Enhancement
        if is_generic(title):
            title = await enhance_with_ai(title, content)
        
        return {
            'text': content['text'],
            'clean_title': title,
            'is_nsfw': is_nsfw,
            'domain': extract_domain(url),
            ...
        }
```

### Curator Agent (Semantic Enhancement)

```python
class CuratorAgent:
    async def process(title, text) -> Dict:
        # 1. AI Analysis (Groq)
        prompt = f"""
        Title: {title}
        Content: {text[:3000]}
        
        Generate:
        1. 3-sentence summary
        2. 5-7 tags
        3. Category
        
        Format: JSON
        """
        
        response = await groq_client.complete(prompt)
        analysis = parse_json(response)
        
        # 2. Embedding Generation
        combined_text = f"{title}. {analysis['summary']}"
        embedding = embedding_service.generate(combined_text)
        
        return {
            'summary': analysis['summary'],
            'tags': analysis['tags'],
            'category': analysis['category'],
            'embedding': embedding
        }
```

---

## Patrones de Diseño Utilizados

### 1. **Agent Pattern**
- Agentes autónomos con responsabilidades específicas
- Comunicación vía orchestrator
- Estado desacoplado

### 2. **Repository Pattern**
- SQLAlchemy models = data layer
- Services = business logic
- Clear separation of concerns

### 3. **Dependency Injection**
- FastAPI's `Depends()` para DB sessions
- Singleton services (embeddings, scraper)
- Configuración centralizada

### 4. **Async/Await Pattern**
- Non-blocking I/O para scraping
- Async database operations
- Concurrent processing

### 5. **Strategy Pattern**
- Embeddings: configurable model
- Safety: extensible keyword/domain lists
- Scraping: fallback strategies

---

## Seguridad y Privacy

### NSFW Detection

```python
# Multi-layer approach:
1. Domain blacklist check
   - pornhub.com, xvideos.com, etc.

2. URL keyword matching
   - /adult/, /xxx/, /18+/, etc.

3. Title analysis
   - Regex pattern matching
   - Threshold: 2+ keywords

4. Content analysis
   - First 1000 chars
   - Keyword frequency
   - Confidence scoring
```

### Local URL Handling

```python
# Detected patterns:
- *.local, *.test
- localhost, 127.0.0.1
- 192.168.x.x, 10.x.x.x

# Action:
- Mark as is_local = true
- Status = manual_required
- No scraping attempted
- Privacy preserved
```

---

## Performance Considerations

### Database Optimization

```sql
-- Índice IVFFlat para búsqueda vectorial
-- lists = sqrt(N) para dataset < 1M
CREATE INDEX ON bookmarks 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- GIN index para arrays
CREATE INDEX ON bookmarks USING gin(tags);

-- B-tree para columnas frecuentemente filtradas
CREATE INDEX ON bookmarks(status);
CREATE INDEX ON bookmarks(category);
```

### Batch Processing

```python
# Import CSV en batches
batch_size = 10  # Configurable

for batch in chunks(bookmarks, batch_size):
    await process_batch(batch)
    await asyncio.sleep(1)  # Rate limiting
```

### Connection Pooling

```python
# SQLAlchemy pool
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,        # Conexiones persistentes
    max_overflow=20,     # Conexiones adicionales
    pool_pre_ping=True   # Health check
)
```

---

## Escalabilidad

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  api:
    deploy:
      replicas: 3  # Load balanced
      
  postgres:
    # Single writer, multiple readers
    # Use pg_pool for read replicas
```

### Caching Strategy

```python
# Futura implementación:
@lru_cache(maxsize=1000)
def get_embedding_cached(text_hash):
    return embedding_service.generate(text)

# Redis para query results
cache_ttl = 3600  # 1 hour
```

---

## Monitoreo y Observabilidad

### Logging

```python
# loguru con niveles
logger.info("Processing bookmark")
logger.warning("NSFW detected")
logger.error("Scraping failed")

# Structured logging
logger.bind(bookmark_id=123, url=url).info("Processing")
```

### Metrics

```python
# ProcessingLog table
- processing_time
- tokens_used
- success_rate
- error_frequency

# Analytics endpoints
GET /stats/processing
GET /stats/categories
GET /stats/tags
```

---

## Extensibilidad

### Agregar Nuevo Agente

```python
class ValidatorAgent:
    """Agente 3: Valida datos estructurados"""
    async def process(bookmark):
        # Custom logic
        return validated_data

# En orchestrator:
result = await self.archivist.process()
result = await self.curator.process(result)
result = await self.validator.process(result)  # ← Nuevo
```

### Cambiar Modelo de Embeddings

```bash
# En .env
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DIMENSION=768

# Requiere migración de datos
python scripts/migrate_embeddings.py
```

### Agregar Fuentes de Datos

```python
# Además de CSV:
class RSSImporter:
    async def import_from_rss(feed_url):
        ...

class BrowserExtensionAPI:
    async def receive_bookmark(bookmark_data):
        ...
```

---

## Testing Strategy

```python
# Unit Tests
tests/
├─ test_agents.py
├─ test_services.py
├─ test_classifiers.py
└─ test_embeddings.py

# Integration Tests
tests/integration/
├─ test_api.py
├─ test_database.py
└─ test_import.py

# E2E Tests
tests/e2e/
└─ test_full_workflow.py
```

---

## Conclusión

Neural Bookmark Brain combina:
- **IA Generativa** (Groq/Llama) para análisis semántico
- **ML Tradicional** (embeddings) para búsqueda vectorial
- **Web Scraping** para adquisición de contenido
- **SQL Moderno** (pgvector) para almacenamiento eficiente

El resultado es un sistema **production-ready** que transforma bookmarks en conocimiento estructurado y buscable.
