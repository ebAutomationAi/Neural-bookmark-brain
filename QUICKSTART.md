# 🚀 Guía de Inicio Rápido - Neural Bookmark Brain

Esta guía te llevará de 0 a búsqueda semántica en **5 minutos**.

---

## ⚡ Inicio Ultra-Rápido (Docker)

### Paso 1: Clonar y Configurar (1 min)

```bash
# Clonar repositorio
git clone <repo-url>
cd neural-bookmark-brain

# Copiar configuración
cp .env.example .env

# Editar .env y añadir tu GROQ_API_KEY
nano .env  # O usa tu editor favorito
```

**Obtener GROQ_API_KEY:**
1. Visita [groq.com](https://groq.com)
2. Crea cuenta gratuita
3. Genera API key
4. Pégala en `.env`

### Paso 2: Levantar Servicios (1 min)

```bash
# Iniciar todo con un comando
docker-compose up -d

# Verificar que todo esté corriendo
docker-compose ps
```

Deberías ver:
```
NAME                   STATUS
neural_bookmark_api    Up
neural_bookmark_db     Up (healthy)
```

### Paso 3: Preparar Datos (30 seg)

```bash
# Opción A: Usar datos de ejemplo
cp data/bookmarks_example.csv data/bookmarks.csv

# Opción B: Usar tus propios bookmarks
# Copia tu CSV con formato: url,title
cp /tu/ruta/bookmarks.csv data/bookmarks.csv
```

### Paso 4: Importar Bookmarks (2 min)

```bash
# Importar con batch de 10 (recomendado)
docker-compose exec api python scripts/import_csv.py data/bookmarks.csv 10

# O usa el Makefile
make import-csv FILE=data/bookmarks.csv
```

**Nota:** El procesamiento toma ~5-10 segundos por bookmark (scraping + AI).

### Paso 5: ¡Buscar! (30 seg)

```bash
# Abrir documentación interactiva
open http://localhost:8000/docs

# O buscar desde terminal
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "limit": 5}'
```

---

## 🎯 Comandos Esenciales

### Ver Estado del Sistema

```bash
# Health check
curl http://localhost:8000/health

# Estadísticas de procesamiento
curl http://localhost:8000/stats/processing

# Top categorías
curl http://localhost:8000/stats/categories
```

### Búsquedas Comunes

```bash
# Búsqueda simple
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "python tutorials", "limit": 10}'

# Filtrar por categoría
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "frameworks",
    "limit": 5,
    "category": "Programación"
  }'

# Incluir NSFW (por defecto está filtrado)
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "content",
    "limit": 10,
    "include_nsfw": true
  }'
```

### Gestión de Bookmarks

```bash
# Listar bookmarks
curl "http://localhost:8000/bookmarks?limit=20"

# Obtener bookmark específico
curl "http://localhost:8000/bookmarks/1"

# Re-procesar bookmark
curl -X POST "http://localhost:8000/process/1"

# Eliminar bookmark
curl -X DELETE "http://localhost:8000/bookmarks/1"
```

---

## 🐛 Troubleshooting Rápido

### ❌ "Connection refused"

```bash
# Verificar que los servicios estén corriendo
docker-compose ps

# Ver logs si algo falló
docker-compose logs -f api
```

### ❌ "API key invalid"

```bash
# Verificar que .env tenga la key correcta
cat .env | grep GROQ_API_KEY

# Debería mostrar: GROQ_API_KEY=gsk_...
# Si muestra "your_groq_api_key_here", edita .env
```

### ❌ "No results found"

```bash
# Verificar que haya bookmarks procesados
curl http://localhost:8000/stats/processing

# Deberías ver "completed" > 0
# Si no, espera a que terminen de procesarse
```

### ❌ "Bookmarks stuck in 'processing'"

```bash
# Ver logs en tiempo real
docker-compose logs -f api

# Re-procesar manualmente
curl -X POST "http://localhost:8000/process/{bookmark_id}"
```

---

## 📱 Uso con el Cliente Python

```python
from scripts.example_api_usage import NeuralBookmarkClient

# Crear cliente
client = NeuralBookmarkClient()

# Buscar
results = client.search("machine learning", limit=5)

# Ver resultados
for result in results['results']:
    print(f"{result['bookmark']['clean_title']}")
    print(f"  Score: {result['similarity_score']:.3f}")
    print(f"  URL: {result['bookmark']['url']}")
```

---

## 🎨 Interfaz Web (Swagger)

Navega a [http://localhost:8000/docs](http://localhost:8000/docs) para:

- ✅ Probar todos los endpoints interactivamente
- ✅ Ver documentación automática
- ✅ Ejecutar búsquedas desde el navegador
- ✅ Ver schemas de respuesta

---

## 🔄 Workflow Típico

1. **Importar bookmarks**: `make import-csv FILE=data/bookmarks.csv`
2. **Esperar procesamiento**: ~5-10 seg por bookmark
3. **Verificar estado**: `curl http://localhost:8000/stats/processing`
4. **Buscar contenido**: Usa `/search` o la interfaz web
5. **Explorar resultados**: Categorías, tags, similitud semántica

---

## ⚙️ Configuración Común

### Cambiar modelo de embeddings (mejor calidad)

```bash
# En .env
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DIMENSION=768

# Reiniciar
docker-compose restart
```

### Ajustar batch size de importación

```bash
# Procesar de 5 en 5 (más lento pero más seguro)
make import-csv FILE=data/bookmarks.csv BATCH=5

# Procesar de 20 en 20 (más rápido)
make import-csv FILE=data/bookmarks.csv BATCH=20
```

### Añadir keywords NSFW personalizadas

```bash
# En .env
NSFW_KEYWORDS=adult,porn,xxx,custom1,custom2,custom3

# Reiniciar
docker-compose restart
```

---

## 📊 Métricas y Monitoreo

```bash
# Ver estadísticas completas
make stats

# Top 20 tags
curl "http://localhost:8000/stats/tags?limit=20"

# Categorías más populares
curl "http://localhost:8000/stats/categories"

# Health check
make health
```

---

## 🚪 Apagar el Sistema

```bash
# Detener sin borrar datos
docker-compose down

# Detener Y borrar TODO (cuidado!)
docker-compose down -v

# O usa Makefile
make down        # Solo detener
make clean       # Borrar todo
```

---

## 🆘 Ayuda Adicional

- **README completo**: [README.md](README.md)
- **Todos los comandos**: `make help`
- **Logs en tiempo real**: `make logs`
- **Shell en el container**: `make shell-api`

---

## ✨ Próximos Pasos

1. Importa tus bookmarks reales
2. Experimenta con búsquedas semánticas
3. Explora las categorías automáticas
4. Descubre tags relevantes
5. Integra con tus workflows

**¡Disfruta tu Neural Bookmark Brain! 🧠✨**
