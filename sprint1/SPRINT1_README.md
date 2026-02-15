# Sprint 1: Implementación de Resiliencia

## 🎯 Objetivo

Transformar el sistema de scraping de "frágil" a "resiliente":
- ✅ Reintentos automáticos con backoff exponencial
- ✅ Rotación de User-Agents
- ✅ Estados parciales (no binario success/fail)
- ✅ Modo fallback URL-only para curación IA
- ✅ Clasificación detallada de errores

---

## 📋 Cambios Implementados

### 1. **Base de Datos** (`migration_001_add_resilience_fields.sql`)
```sql
-- Nuevos campos agregados a tabla bookmarks:
scraping_status         VARCHAR(50)   -- success, failed, partial, skipped
scraping_strategy       VARCHAR(50)   -- trafilatura_retry, beautifulsoup, etc
scraping_error_type     VARCHAR(50)   -- bot_detection, timeout, etc
scraping_attempts       INTEGER       -- Número de intentos
curation_status         VARCHAR(50)   -- success, fallback, failed
curation_mode           VARCHAR(50)   -- full_text, url_only
confidence_score        FLOAT         -- 0.0-1.0 nivel de confianza
```

### 2. **Scraper Resiliente** (`app/services/scraper.py`)
```python
# Antes:
scrape(url) → success/fail (binario)

# Ahora:
scrape(url) → {
    success: bool,
    strategy: "trafilatura_retry" | "beautifulsoup",
    error_type: "bot_detection" | "timeout" | "rate_limited",
    attempts: 3,
    ...
}
```

**Features nuevas:**
- Reintentos automáticos (3 intentos con backoff exponencial)
- Rotación de User-Agents en cada intento
- Cascada de estrategias: Trafilatura → BeautifulSoup
- Clasificación de errores para analytics

### 3. **Curador con Fallback** (`app/agents.py`)
```python
# Modo NORMAL (texto disponible):
curator.process(title, full_text, url)
→ confidence: 1.0
→ mode: "full_text"

# Modo FALLBACK (solo URL):
curator.process(title, None, url)
→ Analiza dominio + path
→ Usa conocimiento previo de IA
→ confidence: 0.5-0.9 (según dominio)
→ mode: "url_only"
```

**Ejemplo real:**
```
URL: https://www.tmb.cat/es/horarios-metro
Sin contenido → IA infiere:
- Category: "Transporte"
- Tags: ["transporte público", "metro", "barcelona"]
- Summary: "Información sobre horarios del metro de Barcelona..."
- Confidence: 0.8 (dominio conocido)
```

### 4. **Estados Parciales**
```python
# Antes (binario):
status: "pending" | "completed" | "failed"

# Ahora (granular):
status: "pending" | "processing" | "completed" | "completed_partial" | "failed" | "manual_required"

# Ejemplo de "completed_partial":
{
    status: "completed_partial",  # ← Éxito parcial
    scraping_status: "failed",     # Scraping falló
    scraping_error_type: "bot_detection",
    curation_status: "fallback",   # Pero curación funcionó
    curation_mode: "url_only",
    confidence_score: 0.7,
    summary: "...",  # ✅ Metadata generada
    tags: [...],     # ✅ Tags disponibles
}
```

---

## 🚀 Instalación (Windows 11)

### Opción A: Script Automático (Recomendado)

```powershell
# 1. Descargar archivos del Sprint 1
# (Ya los tienes en /mnt/user-data/outputs/)

# 2. Ejecutar en modo dry-run (ver qué cambiaría)
.\apply_sprint1.ps1 -DryRun

# 3. Aplicar cambios reales
.\apply_sprint1.ps1 -Force
```

### Opción B: Manual (Paso a Paso)

#### **1. Instalar Dependencias**
```powershell
# Activar entorno virtual si lo usas
# venv\Scripts\Activate.ps1

pip install tenacity==8.2.3
pip install fake-useragent==1.4.0

# Actualizar requirements.txt
Add-Content requirements.txt "tenacity==8.2.3"
Add-Content requirements.txt "fake-useragent==1.4.0"
```

#### **2. Aplicar Migración de Base de Datos**
```powershell
# Copiar archivo SQL al container
docker cp migration_001_add_resilience_fields.sql neural_bookmark_postgres:/tmp/migration.sql

# Ejecutar migración
docker-compose exec postgres psql -U bookmark_user -d neural_bookmarks -f /tmp/migration.sql

# Verificar
docker-compose exec postgres psql -U bookmark_user -d neural_bookmarks -c "SELECT scraping_status, COUNT(*) FROM bookmarks GROUP BY scraping_status;"
```

#### **3. Reemplazar Archivos Python**

**IMPORTANTE**: Haz backup primero
```powershell
# Backup
mkdir backups\sprint1_manual
Copy-Item app\models.py backups\sprint1_manual\
Copy-Item app\services\scraper.py backups\sprint1_manual\
Copy-Item app\agents.py backups\sprint1_manual\

# Reemplazar
Copy-Item models_updated.py app\models.py -Force
Copy-Item scraper_resilient.py app\services\scraper.py -Force
Copy-Item agents_resilient.py app\agents.py -Force
```

#### **4. Reiniciar Sistema**
```powershell
docker-compose restart api

# Ver logs
docker-compose logs -f api
```

#### **5. Verificar Funcionamiento**
```powershell
# Health check
curl http://localhost:8000/health

# Importar bookmark de prueba (URL que bloquea bots)
# Este debería funcionar ahora con fallback
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/process/1"
```

---

## 🧪 Testing

### Test Manual Rápido

```powershell
# 1. Crear CSV de prueba con URLs problemáticas
@"
url,title
https://www.tmb.cat/es/horarios,TMB Horarios
https://httpbin.org/delay/10,Timeout Test
https://example.com/404,Not Found Test
"@ | Out-File -FilePath test_resilience.csv -Encoding UTF8

# 2. Importar
docker-compose exec api python scripts/import_csv.py /tmp/test_resilience.csv 3

# 3. Esperar 30 segundos
Start-Sleep -Seconds 30

# 4. Verificar resultados
Invoke-RestMethod -Uri "http://localhost:8000/stats/processing"

# 5. Ver detalles de estados
docker-compose exec postgres psql -U bookmark_user -d neural_bookmarks -c @"
SELECT 
    url,
    status,
    scraping_status,
    scraping_error_type,
    curation_mode,
    confidence_score,
    category
FROM bookmarks
ORDER BY id DESC
LIMIT 10;
"@
```

### Verificar Nuevas Features

```powershell
# Ver breakdown de errores de scraping
Invoke-RestMethod -Uri "http://localhost:8000/stats/scraping-health"

# Buscar bookmarks con modo fallback
docker-compose exec postgres psql -U bookmark_user -d neural_bookmarks -c @"
SELECT url, curation_mode, confidence_score, category
FROM bookmarks
WHERE curation_mode = 'url_only'
ORDER BY confidence_score DESC;
"@
```

---

## 📊 Métricas de Éxito

### Antes del Sprint 1:
```
Total bookmarks: 100
├─ Completed: 60 (60%)
├─ Failed: 35 (35%)
└─ Pending: 5 (5%)

Failed reasons:
- "Error desconocido": 35
```

### Después del Sprint 1 (Esperado):
```
Total bookmarks: 100
├─ Completed (full): 60 (60%)
├─ Completed (partial): 25 (25%)  ← NUEVO
├─ Failed: 10 (10%)
└─ Pending: 5 (5%)

Failed breakdown:
- bot_detection: 3 (pero con metadata)
- timeout: 2
- dns_error: 1
- unknown: 4

Confidence distribution:
- 1.0 (full scraping): 60
- 0.7-0.9 (url_only conocido): 20
- 0.5-0.6 (url_only desconocido): 5
- 0.0 (completamente fallido): 15
```

**Mejora: De 60% éxito → 85% éxito (incluyendo parciales)**

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'tenacity'"
```powershell
# Solución:
pip install tenacity==8.2.3
```

### Error: "column 'scraping_status' does not exist"
```powershell
# Solución: Migración no aplicada
docker-compose exec postgres psql -U bookmark_user -d neural_bookmarks -f /tmp/migration.sql
```

### Los bookmarks siguen fallando igual
```powershell
# Verificar que los archivos fueron reemplazados
docker-compose exec api python -c "from app.services.scraper import ResilientScraper; print('OK')"

# Si falla: Los archivos no fueron copiados correctamente
```

### Quiero revertir los cambios
```powershell
# Restaurar desde backup
Copy-Item backups\sprint1_*\app\models.py app\models.py -Force
Copy-Item backups\sprint1_*\app\services\scraper.py app\services\scraper.py -Force
Copy-Item backups\sprint1_*\app\agents.py app\agents.py -Force

# Reiniciar
docker-compose restart api
```

---

## 📈 Próximos Pasos (Sprint 2)

1. **Cache local** de contenido scrapeado
2. **Queue system** para procesamiento asíncrono
3. **Internet Archive** como última estrategia
4. **Dashboard** de salud de scraping
5. **Tests automatizados** con pytest

---

## 🤝 Contribución

Si encuentras bugs o tienes sugerencias:
1. Documenta el error con logs
2. Indica qué URL causó el problema
3. Comparte el output de `docker-compose logs api`

---

**¿Preguntas?** Revisa los logs:
```powershell
docker-compose logs -f api | Select-String "Scraper|Curator|Orchestrator"
```