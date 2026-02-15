-- Script de inicialización de PostgreSQL
-- Este script se ejecuta automáticamente al crear el container

-- Habilitar extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Verificar instalación
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Mensaje de confirmación
DO $$
BEGIN
    RAISE NOTICE 'pgvector extension enabled successfully!';
END $$;
