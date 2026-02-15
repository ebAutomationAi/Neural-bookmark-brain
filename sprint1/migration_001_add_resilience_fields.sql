-- Migration 001: Add Resilience Fields
-- Ejecutar: docker-compose exec postgres psql -U bookmark_user -d neural_bookmarks -f /tmp/migration.sql

-- 1. Agregar campos de estado de scraping
ALTER TABLE bookmarks ADD COLUMN IF NOT EXISTS scraping_status VARCHAR(50);
ALTER TABLE bookmarks ADD COLUMN IF NOT EXISTS scraping_strategy VARCHAR(50);
ALTER TABLE bookmarks ADD COLUMN IF NOT EXISTS scraping_error_type VARCHAR(50);
ALTER TABLE bookmarks ADD COLUMN IF NOT EXISTS scraping_attempts INTEGER DEFAULT 0;

-- 2. Agregar campos de estado de curación
ALTER TABLE bookmarks ADD COLUMN IF NOT EXISTS curation_status VARCHAR(50);
ALTER TABLE bookmarks ADD COLUMN IF NOT EXISTS curation_mode VARCHAR(50);

-- 3. Agregar métricas de calidad
ALTER TABLE bookmarks ADD COLUMN IF NOT EXISTS confidence_score FLOAT DEFAULT 0.0;

-- 4. Actualizar registros existentes con valores por defecto
UPDATE bookmarks 
SET 
    scraping_status = CASE 
        WHEN status = 'completed' THEN 'success'
        WHEN status = 'failed' THEN 'failed'
        ELSE 'pending'
    END,
    curation_status = CASE 
        WHEN status = 'completed' THEN 'success'
        WHEN status = 'failed' THEN 'failed'
        ELSE 'pending'
    END,
    curation_mode = CASE 
        WHEN full_text IS NOT NULL THEN 'full_text'
        ELSE 'url_only'
    END,
    confidence_score = CASE 
        WHEN status = 'completed' AND full_text IS NOT NULL THEN 1.0
        WHEN status = 'completed' AND full_text IS NULL THEN 0.6
        ELSE 0.0
    END
WHERE scraping_status IS NULL;

-- 5. Crear índices para nuevos campos
CREATE INDEX IF NOT EXISTS idx_scraping_status ON bookmarks(scraping_status);
CREATE INDEX IF NOT EXISTS idx_confidence_score ON bookmarks(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_scraping_error_type ON bookmarks(scraping_error_type) WHERE scraping_error_type IS NOT NULL;

-- Verificación
SELECT 
    scraping_status,
    COUNT(*) as count,
    AVG(confidence_score) as avg_confidence
FROM bookmarks
GROUP BY scraping_status;