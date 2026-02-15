# tests/manual/smoke_test.sh
#!/bin/bash
set -e

echo "🔥 SMOKE TEST - Neural Bookmark Brain"
echo "======================================"

# 1. Sistema levantado
echo "✓ Verificando containers..."
docker-compose ps | grep -q "Up" || exit 1

# 2. Health check
echo "✓ Health check..."
curl -f http://localhost:8000/health || exit 1

# 3. Importar CSV pequeño
echo "✓ Importando 3 bookmarks de prueba..."
cat > /tmp/test_bookmarks.csv << EOF
url,title
https://fastapi.tiangolo.com,FastAPI Docs
https://www.postgresql.org,PostgreSQL
https://github.com/pgvector/pgvector,pgvector
EOF

docker-compose exec -T api python scripts/import_csv.py /tmp/test_bookmarks.csv 3

# 4. Esperar procesamiento
echo "⏳ Esperando procesamiento (30s)..."
sleep 30

# 5. Verificar stats
echo "✓ Verificando stats..."
COMPLETED=$(curl -s http://localhost:8000/stats/processing | jq .completed)
if [ "$COMPLETED" -lt 1 ]; then
    echo "❌ No hay bookmarks completados"
    exit 1
fi

# 6. Búsqueda semántica
echo "✓ Probando búsqueda semántica..."
RESULTS=$(curl -s -X POST http://localhost:8000/search \
    -H "Content-Type: application/json" \
    -d '{"query":"python web framework","limit":5}' | jq .total)

if [ "$RESULTS" -lt 1 ]; then
    echo "❌ Búsqueda no retorna resultados"
    exit 1
fi

echo ""
echo "✅ TODOS LOS TESTS PASARON"
echo "Bookmarks completados: $COMPLETED"
echo "Resultados de búsqueda: $RESULTS"