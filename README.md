# 🧠 Neural Bookmark Brain

**Sistema de Base de Conocimiento Semántico potenciado por IA**

Transforma una lista desordenada de bookmarks en una base de conocimiento inteligente, categorizada y semánticamente buscable usando Agentes de IA.

---

## 🌟 Características Principales

### 🤖 Sistema Dual de Agentes IA

1. **Agente Archivista (The Gatekeeper)**
   - Validación y normalización de URLs
   - Web scraping con Trafilatura
   - Detección automática de contenido NSFW
   - Limpieza de títulos genéricos
   - Manejo especial de URLs locales (.test, .local, localhost)

2. **Agente Curador (The Librarian)**
   - Generación de resúmenes (3 oraciones)
   - Creación automática de tags temáticos
   - Clasificación por categorías
   - Generación de embeddings semánticos

### 🔍 Búsqueda Semántica

- Búsqueda por **significado**, no solo por palabras clave
- Powered by `pgvector` + `sentence-transformers`
- Filtros avanzados: categoría, tags, NSFW
- Scores de similitud coseno

### 🔒 Privacy-First & Safety

- **Detección automática de NSFW** (adulto, explícito)
- Filtrado por keywords y dominios bloqueados
- Manejo especial de URLs locales (no scraped)
- Datos sensibles nunca expuestos en dashboards públicos

### 📊 API REST Completa

- FastAPI con documentación automática (Swagger/ReDoc)
- Endpoints de búsqueda, listado, estadísticas
- Re-procesamiento manual de bookmarks
- Health checks y monitoreo

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────┐
│                  CSV Input                          │
│              (url, title)                           │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│         Import Script (import_csv.py)               │
│  - Validación URLs                                  │
│  - Detección duplicados                             │
│  - Creación registros iniciales                     │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│      Orchestrator (Agent Coordinator)               │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌──────────────┐    ┌──────────────────┐
│  AGENT 1     │    │    AGENT 2       │
│  Archivist   │───▶│    Curator       │
│              │    │                  │
│ • Scraping   │    │ • AI Summary     │
│ • NSFW Check │    │ • Tags Gen       │
│ • Title Fix  │    │ • Category       │
│ • Local Det. │    │ • Embeddings     │
└──────────────┘    └──────────────────┘
        │                     │
        └──────────┬──────────┘
                   ▼
┌─────────────────────────────────────────────────────┐
│     PostgreSQL + pgvector                           │
│  - Bookmarks (con embeddings)                       │
│  - Processing Logs                                  │
│  - Search History                                   │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│          FastAPI REST API                           │
│  - /search (semantic search)                        │
│  - /bookmarks (CRUD)                                │
│  - /stats (analytics)                               │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Inicio Rápido

### Prerrequisitos

- Docker & Docker Compose
- Python 3.11+
- Groq API Key (obtener en [groq.com](https://groq.com))

### 1. Clonar y Configurar

```bash
# Clonar repositorio
git clone <repo-url>
cd neural-bookmark-brain

# Copiar y configurar variables de entorno
cp .env.example .env

# Editar .env y añadir tu GROQ_API_KEY
nano .env
```

### 2. Levantar Servicios con Docker

```bash
# Iniciar PostgreSQL + API
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### 3. Importar Bookmarks

```bash
# Copiar tu CSV de bookmarks
cp /path/to/your/bookmarks.csv data/bookmarks.csv

# Importar (desde el container)
docker-compose exec api python scripts/import_csv.py data/bookmarks.csv 10

# O desde local (si tienes Python configurado)
python scripts/import_csv.py data/bookmarks.csv 10
```

**Formato CSV requerido:**
```csv
url,title
https://example.com,Example Site
https://github.com/user/repo,My Repo
```

### 4. Acceder a la API

```bash
# API Docs (Swagger)
http://localhost:8000/docs

# ReDoc
http://localhost:8000/redoc

# Health Check
curl http://localhost:8000/health
```

---

## 📖 Uso de la API

### Búsqueda Semántica

```bash
# Búsqueda básica
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning tutorials",
    "limit": 10
  }'

# Con filtros
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "python frameworks",
    "limit": 5,
    "category": "Programación",
    "include_nsfw": false
  }'
```

### Listar Bookmarks

```bash
# Primeros 50 bookmarks
curl "http://localhost:8000/bookmarks?limit=50"

# Filtrar por categoría
curl "http://localhost:8000/bookmarks?category=Tecnología&limit=20"

# Solo completados
curl "http://localhost:8000/bookmarks?status_filter=completed"
```

### Estadísticas

```bash
# Estado de procesamiento
curl "http://localhost:8000/stats/processing"

# Top categorías
curl "http://localhost:8000/stats/categories"

# Top tags
curl "http://localhost:8000/stats/tags?limit=20"
```

### Re-procesar Bookmark

```bash
# Re-procesar un bookmark específico
curl -X POST "http://localhost:8000/process/123"
```

---

## 🛠️ Desarrollo Local (Sin Docker)

### 1. Configurar Base de Datos

```bash
# Instalar PostgreSQL + pgvector
# Ubuntu/Debian
sudo apt-get install postgresql-14 postgresql-14-pgvector

# Crear database
sudo -u postgres createdb neural_bookmarks
sudo -u postgres psql neural_bookmarks -c "CREATE EXTENSION vector;"
```

### 2. Configurar Python

```bash
# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar Variables

```bash
# Editar .env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/neural_bookmarks
GROQ_API_KEY=your_key_here
```

### 4. Inicializar DB

```bash
python scripts/init_db.py
```

### 5. Ejecutar API

```bash
# Modo desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🧪 Testing

```bash
# Ejecutar tests (cuando estén disponibles)
pytest tests/ -v

# Con coverage
pytest tests/ --cov=app --cov-report=html
```

---

## 📊 Casos de Uso

### 1. Biblioteca Personal de Conocimiento
- Organiza automáticamente tus bookmarks por temas
- Búsqueda semántica: "frameworks para APIs en Python"
- Tags automáticos para descubrimiento

### 2. Research Assistant
- Procesa papers, artículos, documentación
- Genera resúmenes de 3 oraciones
- Encuentra contenido relacionado semánticamente

### 3. Content Curation
- Detecta y filtra contenido NSFW automáticamente
- Categorización temática inteligente
- Dashboard limpio y profesional

### 4. Team Knowledge Base
- Base de datos compartida de recursos
- Búsqueda inteligente para el equipo
- Analytics de contenido más relevante

---

## 🔧 Configuración Avanzada

### Ajustar Modelo de Embeddings

```python
# En .env
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DIMENSION=768
```

Modelos recomendados:
- `all-MiniLM-L6-v2` (384 dim) - Rápido, eficiente
- `all-mpnet-base-v2` (768 dim) - Mejor calidad
- `paraphrase-multilingual-mpnet-base-v2` (768 dim) - Multilenguaje

### Personalizar Keywords NSFW

```bash
# En .env, añadir más keywords separadas por comas
NSFW_KEYWORDS=adult,porn,xxx,custom1,custom2
NSFW_DOMAINS=example-nsfw.com,other-domain.com
```

### Ajustar Parámetros de Groq

```bash
# En .env
GROQ_MODEL=llama-3.1-70b-versatile
GROQ_TEMPERATURE=0.3
GROQ_MAX_TOKENS=2048
```

---

## 📁 Estructura del Proyecto

```
neural-bookmark-brain/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuración
│   ├── database.py          # SQLAlchemy async
│   ├── models.py            # Modelos DB
│   ├── schemas.py           # Pydantic schemas
│   ├── agents.py            # ⭐ Sistema de Agentes IA
│   ├── services/
│   │   ├── scraper.py       # Trafilatura scraping
│   │   ├── classifier.py    # NSFW detection
│   │   └── embeddings.py    # Vector embeddings
│   └── utils/
│       └── validators.py    # Validaciones
├── scripts/
│   ├── import_csv.py        # ⭐ Importador CSV
│   ├── init_db.py           # DB initialization
│   └── init_db.sql          # SQL setup
├── data/
│   └── bookmarks.csv        # Tu CSV aquí
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🐛 Troubleshooting

### Error: "Extension vector not found"

```bash
# Verificar que pgvector esté instalado
docker-compose exec postgres psql -U bookmark_user -d neural_bookmarks -c "SELECT * FROM pg_extension WHERE extname='vector';"

# Reinstalar si es necesario
docker-compose down -v
docker-compose up -d
```

### Error: "Groq API key invalid"

```bash
# Verificar que .env tenga la key correcta
cat .env | grep GROQ_API_KEY

# Reiniciar containers
docker-compose restart
```

### Bookmarks no se procesan

```bash
# Ver logs del container
docker-compose logs -f api

# Revisar estado en DB
docker-compose exec postgres psql -U bookmark_user -d neural_bookmarks -c "SELECT status, COUNT(*) FROM bookmarks GROUP BY status;"

# Re-procesar manualmente
curl -X POST "http://localhost:8000/process/{bookmark_id}"
```

### Búsqueda no retorna resultados

```bash
# Verificar que haya embeddings generados
curl "http://localhost:8000/stats/processing"

# Revisar si hay bookmarks completados
curl "http://localhost:8000/bookmarks?status_filter=completed&limit=5"
```

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas! Por favor:

1. Fork del repositorio
2. Crear branch para feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

---

## 📝 Roadmap

- [ ] Dashboard web con React/Vue
- [ ] Exportar a Notion/Obsidian
- [ ] Browser extension para captura automática
- [ ] Soporte para imágenes/PDFs
- [ ] Integración con Chrome/Firefox
- [ ] Fine-tuning de embeddings
- [ ] Multi-usuario con auth
- [ ] Mobile app

---

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE) para más detalles

---

## 🙏 Agradecimientos

- **Groq** - API de LLMs ultra-rápida
- **Trafilatura** - Extracción de contenido web
- **pgvector** - Vector similarity search en PostgreSQL
- **Sentence Transformers** - Embeddings semánticos
- **FastAPI** - Framework web moderno

---

## 📧 Contacto

¿Preguntas? ¿Sugerencias? Abre un issue en GitHub!

**Happy Bookmarking! 🚀**
