# 🔒 Rate Limiting - Protección de la API

El sistema implementa **rate limiting** para proteger la API de abusos y sobrecarga.

## 📊 Límites Configurados

| Endpoint | Límite por Defecto | Variable de Config |
|----------|-------------------|-------------------|
| **Búsqueda** (`/search`) | 10 peticiones/minuto | `RATE_LIMIT_SEARCH` |
| **Crear Bookmark** (`/bookmarks`) | 5 peticiones/minuto | `RATE_LIMIT_CREATE` |
| **Reprocesar** (`/process/{id}`) | 5 peticiones/minuto | `RATE_LIMIT_CREATE` |
| **Global** (todos los endpoints) | 100 peticiones/minuto | `RATE_LIMIT_GLOBAL` |

## ⚙️ Configuración

Las variables se configuran en el archivo `.env`:

```bash
# Rate Limiting (API Protection)
RATE_LIMIT_ENABLED=true
RATE_LIMIT_SEARCH=10/minute
RATE_LIMIT_CREATE=5/minute
RATE_LIMIT_GLOBAL=100/minute
```

### Formatos Soportados

El rate limiting soporta varios formatos:

```bash
# Por minuto
RATE_LIMIT_SEARCH=10/minute

# Por hora
RATE_LIMIT_SEARCH=100/hour

# Por día
RATE_LIMIT_SEARCH=1000/day

# Por segundo
RATE_LIMIT_SEARCH=1/second
```

## 🛡️ Cómo Funciona

### Identificación de Clientes
- Los límites se aplican **por IP address**
- Se usa la IP del cliente (detectada con `get_remote_address`)
- Compatible con proxies inversos (X-Forwarded-For)

### Respuesta cuando se excede el límite

Cuando un cliente excede el rate limit, recibe:

**Status Code:** `429 Too Many Requests`

**Response:**
```json
{
  "error": "Rate limit exceeded: 10 per 1 minute"
}
```

**Headers:**
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1644441600
Retry-After: 60
```

## 📝 Endpoints Protegidos

### POST `/search` - Búsqueda Semántica
**Límite:** 10/minute

```python
@limiter.limit(settings.RATE_LIMIT_SEARCH)
async def semantic_search(req: Request, ...):
    ...
```

**Razón:** Las búsquedas semánticas son costosas computacionalmente (embeddings + vector search)

### POST `/bookmarks` - Crear Bookmark
**Límite:** 5/minute

```python
@limiter.limit(settings.RATE_LIMIT_CREATE)
async def create_bookmark(req: Request, ...):
    ...
```

**Razón:** Previene spam y creación masiva automatizada

### POST `/process/{bookmark_id}` - Reprocesar
**Límite:** 5/minute

```python
@limiter.limit(settings.RATE_LIMIT_CREATE)
async def reprocess_bookmark(req: Request, ...):
    ...
```

**Razón:** El reprocesamiento consume recursos (scraping + AI)

## 🧪 Testing

### Script de Test Manual

```bash
python tests/test_rate_limiting_api.py
```

Este script:
1. Verifica que endpoints sin límite funcionan
2. Hace 10 búsquedas (debería pasar)
3. Hace una búsqueda más (debería fallar con 429)
4. Repite para endpoints de creación

### Test con curl

```bash
# Hacer 11 búsquedas rápidas (la #11 debería fallar)
for i in {1..11}; do
  echo "Petición $i:"
  curl -X POST http://localhost:8000/search \
    -H "Content-Type: application/json" \
    -d '{"query":"test","limit":5}' \
    -w "\nStatus: %{http_code}\n\n"
done
```

### Test con Python

```python
import httpx
import asyncio

async def test_rate_limit():
    async with httpx.AsyncClient() as client:
        for i in range(12):
            response = await client.post(
                "http://localhost:8000/search",
                json={"query": "test", "limit": 5}
            )
            print(f"Petición {i+1}: {response.status_code}")
            await asyncio.sleep(0.5)

asyncio.run(test_rate_limit())
```

## 🔧 Personalización

### Ajustar Límites por Entorno

**Desarrollo Local** (más permisivo):
```bash
RATE_LIMIT_SEARCH=50/minute
RATE_LIMIT_CREATE=20/minute
RATE_LIMIT_GLOBAL=500/minute
```

**Producción** (más restrictivo):
```bash
RATE_LIMIT_SEARCH=10/minute
RATE_LIMIT_CREATE=3/minute
RATE_LIMIT_GLOBAL=50/minute
```

**API Interna** (sin límites):
```bash
RATE_LIMIT_ENABLED=false
```

### Añadir Rate Limit a Nuevos Endpoints

```python
@app.get("/my-endpoint")
@limiter.limit("20/minute")  # Límite específico
async def my_endpoint(req: Request):
    return {"message": "hello"}
```

### Excluir un Endpoint

```python
@app.get("/public-endpoint")
@limiter.exempt  # Sin rate limit
async def public_endpoint():
    return {"message": "no limit"}
```

## 🌐 Compatibilidad con Proxies

Si usas nginx, Cloudflare, o cualquier proxy inverso, configura:

```python
# En app/main.py
from slowapi.util import get_remote_address

# Por defecto usa X-Forwarded-For si está presente
limiter = Limiter(key_func=get_remote_address)
```

### Nginx Configuration

```nginx
location / {
    proxy_pass http://backend;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## 📊 Monitoring

### Ver Límites Actuales

Los límites se incluyen en los headers de respuesta:

```bash
curl -I http://localhost:8000/search \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"query":"test"}'
```

Response headers:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 9
X-RateLimit-Reset: 1644441660
```

### Logging

El sistema loggea automáticamente cuando se exceden límites:

```
[WARNING] Rate limit exceeded for IP 192.168.1.100 on /search
```

## 🚨 Troubleshooting

### "429 Too Many Requests" en desarrollo

**Problema:** Estás desarrollando y te bloqueas constantemente

**Solución:**
```bash
# Aumentar límites en .env
RATE_LIMIT_SEARCH=100/minute
RATE_LIMIT_CREATE=50/minute
```

O temporalmente deshabilitar:
```bash
RATE_LIMIT_ENABLED=false
```

### Rate limit no funciona

**Verificar:**
1. ¿Está `slowapi` instalado? → `pip install slowapi`
2. ¿Está la configuración cargada? → Revisar logs de startup
3. ¿Estás usando `Request` en el endpoint?

```python
# ❌ Incorrecto
async def my_endpoint():
    ...

# ✅ Correcto
async def my_endpoint(req: Request):
    ...
```

### Límites se resetean muy rápido

El rate limiting usa **ventana deslizante** (sliding window), no ventana fija.

- ✅ Más justo y preciso
- ⚠️ Puede parecer que se resetea rápido

## 🔐 Seguridad Adicional

### Recomendaciones

1. **Usar HTTPS en producción**
2. **Implementar autenticación** para APIs sensibles
3. **Monitoring activo** de tráfico inusual
4. **Cloudflare** o WAF para protección DDoS adicional

### Complementar con IP Whitelist

```python
ALLOWED_IPS = ["192.168.1.100", "10.0.0.1"]

@app.middleware("http")
async def ip_whitelist(request: Request, call_next):
    client_ip = get_remote_address(request)
    if client_ip not in ALLOWED_IPS:
        return JSONResponse(
            status_code=403,
            content={"error": "IP not allowed"}
        )
    return await call_next(request)
```

## 📚 Referencias

- [slowapi Documentation](https://slowapi.readthedocs.io/)
- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- [HTTP 429 Status Code](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429)
