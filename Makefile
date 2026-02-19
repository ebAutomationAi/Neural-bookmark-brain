.PHONY: help build up down logs restart clean import-csv init-db test

help: ## Muestra esta ayuda
	@echo "Neural Bookmark Brain - Comandos disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Construye las imágenes Docker
	docker-compose build

up: ## Levanta los servicios
	docker-compose up -d
	@echo "✅ Servicios iniciados"
	@echo "📖 API Docs: http://localhost:8000/docs"

down: ## Detiene los servicios
	docker-compose down

logs: ## Muestra logs de los servicios
	docker-compose logs -f

restart: ## Reinicia los servicios
	docker-compose restart

clean: ## Elimina containers, volúmenes y datos
	docker-compose down -v
	@echo "⚠️  Todos los datos han sido eliminados"

init-db: ## Inicializa la base de datos
	docker-compose exec api python scripts/init_db.py

import-csv: ## Importa bookmarks desde CSV (usar: make import-csv FILE=data/bookmarks.csv)
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Error: Especifica el archivo CSV"; \
		echo "Uso: make import-csv FILE=data/bookmarks.csv"; \
		exit 1; \
	fi
	docker-compose exec api python scripts/import_csv.py $(FILE)

stats: ## Muestra estadísticas de procesamiento
	@curl -s http://localhost:8000/stats/processing | python -m json.tool

health: ## Health check del sistema
	@curl -s http://localhost:8000/health | python -m json.tool

search: ## Búsqueda de ejemplo (usar: make search QUERY="machine learning")
	@if [ -z "$(QUERY)" ]; then \
		QUERY="python programming"; \
	fi
	@curl -s -X POST "http://localhost:8000/search" \
		-H "Content-Type: application/json" \
		-d '{"query": "$(QUERY)", "limit": 5}' | python -m json.tool

shell-api: ## Abre shell en el container de la API
	docker-compose exec api /bin/bash

shell-db: ## Abre psql en PostgreSQL
	docker-compose exec postgres psql -U bookmark_user -d neural_bookmarks

backup-db: ## Backup de la base de datos
	@mkdir -p backups
	docker-compose exec postgres pg_dump -U bookmark_user neural_bookmarks > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup creado en backups/"

restore-db: ## Restaura base de datos (usar: make restore-db FILE=backups/backup.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Error: Especifica el archivo de backup"; \
		echo "Uso: make restore-db FILE=backups/backup.sql"; \
		exit 1; \
	fi
	docker-compose exec -T postgres psql -U bookmark_user -d neural_bookmarks < $(FILE)

test: ## Ejecuta tests (cuando estén disponibles)
	docker-compose exec api pytest tests/ -v

dev: ## Modo desarrollo (con reload)
	docker-compose up

install-local: ## Instala dependencias localmente (sin Docker)
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Entorno virtual creado. Activar con: source venv/bin/activate"

security-check: ## Ejecuta análisis de seguridad en dependencias locales
	@echo "🔍 Configurando entorno virtual seguro para herramientas..."
	@python3 -m venv .venv-security
	@.venv-security/bin/pip install -q --upgrade pip
	@.venv-security/bin/pip install -q safety pip-audit
	@echo "\n🛡️  Ejecutando Safety Check..."
	@.venv-security/bin/safety check -r requirements.txt || true
	@echo "\n🛡️  Ejecutando Pip-Audit..."
	@.venv-security/bin/pip-audit -r requirements.txt || true
	@echo "\n🧹 Limpiando entorno..."
	@rm -rf .venv-security

update-deps: ## Lista dependencias desactualizadas
	@echo "📦 Buscando paquetes desactualizados..."
	@python3 -m venv .venv-security
	@.venv-security/bin/pip install -q -r requirements.txt
	@.venv-security/bin/pip list --outdated
	@rm -rf .venv-security