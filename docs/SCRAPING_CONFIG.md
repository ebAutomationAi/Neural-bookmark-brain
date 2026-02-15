# ⚙️ Configuración del Scraper

El sistema incluye un scraper resiliente con múltiples estrategias de extracción y configuraciones para evitar bloqueos y respetar los servidores.

## 🔧 Variables de Configuración

Todas estas variables se configuran en el archivo `.env`:

### `SCRAPER_TIMEOUT`
- **Valor por defecto**: `30` (segundos)
- **Descripción**: Tiempo máximo de espera para una petición HTTP
- **Rango recomendado**: 10-60 segundos

```bash
SCRAPER_TIMEOUT=30
```

### `SCRAPER_MAX_RETRIES`
- **Valor por defecto**: `3`
- **Descripción**: Número máximo de reintentos en caso de error temporal
- **Rango recomendado**: 2-5 reintentos

```bash
SCRAPER_MAX_RETRIES=3
```

### `SCRAPER_DELAY_BETWEEN_REQUESTS`
- **Valor por defecto**: `1.0` (segundos)
- **Descripción**: Tiempo de espera entre peticiones consecutivas (rate limiting)
- **Rango recomendado**: 0.5-2.0 segundos
- **⚠️ Importante**: Valores muy bajos pueden causar bloqueos por rate limiting

```bash
SCRAPER_DELAY_BETWEEN_REQUESTS=1.0
```

### `SCRAPER_MAX_REDIRECTS`
- **Valor por defecto**: `5`
- **Descripción**: Número máximo de redirecciones HTTP a seguir
- **Rango recomendado**: 3-10 redirecciones

```bash
SCRAPER_MAX_REDIRECTS=5
```

### `SCRAPER_USER_AGENT`
- **Valor por defecto**: `Mozilla/5.0 (compatible; NeuralBookmarkBot/1.0)`
- **Descripción**: User-Agent usado en las peticiones HTTP
- **Nota**: El sistema también rota entre diferentes user-agents realistas

```bash
SCRAPER_USER_AGENT=Mozilla/5.0 (compatible; NeuralBookmarkBot/1.0)
```

## 🚀 Estrategias de Scraping

El scraper implementa un sistema de **fallback** con múltiples estrategias:

### 1️⃣ Estrategia Principal: Trafilatura
- Extracción optimizada de contenido principal
- Eliminación automática de ads y navegación
- Mejor calidad de texto extraído

### 2️⃣ Estrategia Fallback: BeautifulSoup
- Se activa cuando Trafilatura falla o detecta bot (403)
- Extracción más básica pero menos detectable
- Mayor compatibilidad con sitios difíciles

## 🛡️ Protecciones Implementadas

### Rate Limiting
```python
# Espera automática entre peticiones
await scraper._rate_limit()
```

El sistema espera automáticamente `SCRAPER_DELAY_BETWEEN_REQUESTS` segundos entre cada petición para evitar:
- Bloqueos por rate limiting (429)
- Sobrecarga de servidores
- Detección como bot

### Timeout
```python
async with httpx.AsyncClient(timeout=self.timeout) as client:
    response = await client.get(url)
```

Todas las peticiones tienen un timeout configurado para evitar bloqueos indefinidos.

### Límite de Redirecciones
```python
async with httpx.AsyncClient(max_redirects=self.max_redirects) as client:
    response = await client.get(url)
```

Previene loops infinitos de redirecciones.

### Reintentos Inteligentes
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError))
)
```

Reintenta automáticamente ante errores temporales con espera exponencial.

## 📊 Manejo de Errores

El scraper clasifica los errores en categorías:

| Tipo de Error | Descripción | Estrategia |
|--------------|-------------|-----------|
| `bot_detection` | 403 Forbidden | Cambiar a BeautifulSoup |
| `rate_limited` | 429 Too Many Requests | Esperar más tiempo |
| `timeout` | Timeout de conexión | Reintentar |
| `connection_refused` | Servidor no responde | Reintentar |
| `too_many_redirects` | > max_redirects | Fallar |
| `insufficient_content` | Texto muy corto | Cambiar a BeautifulSoup |
| `local_url` | URL local (.test, localhost) | Marcar para manual |

## 🧪 Testing

Ejecutar tests de rate limiting:

```bash
python tests/test_rate_limiting.py
```

O con pytest:

```bash
pytest tests/test_rate_limiting.py -v
```

## 💡 Recomendaciones

### Para Desarrollo Local
```bash
SCRAPER_TIMEOUT=15
SCRAPER_MAX_RETRIES=2
SCRAPER_DELAY_BETWEEN_REQUESTS=0.5
SCRAPER_MAX_REDIRECTS=5
```

### Para Producción
```bash
SCRAPER_TIMEOUT=30
SCRAPER_MAX_RETRIES=3
SCRAPER_DELAY_BETWEEN_REQUESTS=1.5
SCRAPER_MAX_REDIRECTS=5
```

### Para Scraping Intensivo
```bash
SCRAPER_TIMEOUT=45
SCRAPER_MAX_RETRIES=5
SCRAPER_DELAY_BETWEEN_REQUESTS=2.0
SCRAPER_MAX_REDIRECTS=10
```

## ⚠️ Consideraciones Éticas

- **Respeta robots.txt**: Aunque no está implementado automáticamente, considera verificar manualmente
- **Rate limiting**: No sobrecargues servidores externos
- **User-Agent honesto**: Identifica tu bot claramente
- **URLs locales**: Las URLs `.local`, `.test`, `localhost` no se scrapean automáticamente

## 🐛 Troubleshooting

### Muchos errores 403 (Bot Detection)
- Aumenta `SCRAPER_DELAY_BETWEEN_REQUESTS`
- El sistema automáticamente cambiará a BeautifulSoup

### Timeouts frecuentes
- Aumenta `SCRAPER_TIMEOUT`
- Verifica tu conexión a internet
- Algunos sitios son inherentemente lentos

### Rate Limiting (429)
- Aumenta `SCRAPER_DELAY_BETWEEN_REQUESTS` a 2.0 o más
- Reduce `SCRAPER_MAX_RETRIES` temporalmente

### Loops de redirecciones
- Aumenta `SCRAPER_MAX_REDIRECTS` si es legítimo
- O reporta la URL como problemática
