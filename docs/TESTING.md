# Cómo testear la app

## 1. Preparar el entorno

```bash
cd /home/kiko/docker_apps/Neural-bookmark-brain

# Crear y activar venv (recomendado)
python3 -m venv venv
source venv/bin/activate   # Linux/macOS

# Instalar dependencias
pip install -r requirements.txt
```

## 2. Tests unitarios (sin base de datos)

No necesitan PostgreSQL ni `.env` cargado (sí hace falta que la app importe, así que `DATABASE_URL` y `GROQ_API_KEY` pueden estar en `.env` vacíos o con valores de prueba).

```bash
pytest tests/unit -v
```

Incluye: `test_validators.py`, `test_classifier.py`, `test_embeddings.py`.

## 3. Probar la API en marcha

### Opción A: Docker Compose

```bash
docker-compose up -d
# API en http://localhost:8090
curl -s http://localhost:8090/health
curl -s http://localhost:8090/
```

Documentación: http://localhost:8090/docs

### Opción B: Uvicorn en local

Con PostgreSQL y `.env` configurados:

```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# API en http://localhost:8000
```

## 4. Tests de integración (con base de datos de prueba)

Necesitan PostgreSQL con una base de datos solo para tests.

**Crear la base de datos de test:**

```bash
# Con PostgreSQL en local (mismo usuario/contraseña que en .env o conftest)
createdb neural_bookmarks_test
psql -d neural_bookmarks_test -c "CREATE EXTENSION vector;"
```

El `conftest` usa por defecto:

`postgresql+asyncpg://bookmark_user:bookmark_pass_2024@localhost:5432/neural_bookmarks_test`

Si usas otras credenciales, cambia `TEST_DATABASE_URL` en `tests/conftest.py` o define las variables de entorno que use tu config.

**Ejecutar tests de integración:**

```bash
pytest tests/integration -v
```

## 5. Ejecutar todos los tests

```bash
pytest tests/ -v
```

Los tests que requieren `db_session` usan la base de datos de test; el resto (health, root, etc.) usa la app con su configuración normal.

## 6. Tests que fallan por falta de dependencias

- **ModuleNotFoundError (sqlalchemy, app, etc.):** activar el venv e instalar con `pip install -r requirements.txt`.
- **DATABASE_URL no configurada:** tener un `.env` con `DATABASE_URL` (o exportarla); para solo tests unitarios puede ser una URL de prueba.
- **slowapi:** está en `requirements.txt`; si falla el import, `pip install slowapi`.
