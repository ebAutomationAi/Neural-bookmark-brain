# apply_sprint1.ps1
# Script para aplicar Sprint 1: Resiliencia y Estados Parciales

param(
    [switch]$DryRun,
    [switch]$Force
)

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  SPRINT 1: Implementación de Resiliencia" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Rutas
$ProjectRoot = Get-Location
$BackupDir = Join-Path $ProjectRoot "backups\sprint1_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# Función de backup
function Backup-File {
    param([string]$FilePath)
    
    if (Test-Path $FilePath) {
        $BackupPath = Join-Path $BackupDir $FilePath
        $BackupFolder = Split-Path $BackupPath -Parent
        
        if (-not (Test-Path $BackupFolder)) {
            New-Item -ItemType Directory -Path $BackupFolder -Force | Out-Null
        }
        
        Copy-Item $FilePath $BackupPath -Force
        Write-Host "  ✅ Backup: $FilePath" -ForegroundColor Green
    }
}

# 1. Crear directorio de backup
Write-Host "[1/7] Creando backup..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

# 2. Backup de archivos existentes
Write-Host "[2/7] Respaldando archivos originales..." -ForegroundColor Yellow
Backup-File "app\models.py"
Backup-File "app\services\scraper.py"
Backup-File "app\agents.py"

if ($DryRun) {
    Write-Host ""
    Write-Host "⚠️  MODO DRY-RUN: No se aplicarán cambios" -ForegroundColor Yellow
    Write-Host "   Backup creado en: $BackupDir" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Para aplicar cambios reales, ejecuta:" -ForegroundColor White
    Write-Host "  .\apply_sprint1.ps1 -Force" -ForegroundColor Cyan
    exit 0
}

if (-not $Force) {
    Write-Host ""
    Write-Host "⚠️  ADVERTENCIA: Esto modificará archivos del proyecto" -ForegroundColor Yellow
    $confirm = Read-Host "¿Continuar? (yes/no)"
    
    if ($confirm -ne "yes") {
        Write-Host "Operación cancelada" -ForegroundColor Yellow
        exit 0
    }
}

# 3. Instalar dependencias nuevas
Write-Host ""
Write-Host "[3/7] Instalando dependencias nuevas..." -ForegroundColor Yellow
try {
    pip install tenacity==8.2.3 fake-useragent==1.4.0 --quiet
    
    # Actualizar requirements.txt
    $reqFile = "requirements.txt"
    $newDeps = @("tenacity==8.2.3", "fake-useragent==1.4.0")
    
    $existingDeps = Get-Content $reqFile -ErrorAction SilentlyContinue
    
    foreach ($dep in $newDeps) {
        if ($existingDeps -notcontains $dep) {
            Add-Content $reqFile $dep
            Write-Host "  ✅ Agregado a requirements.txt: $dep" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "  ❌ Error instalando dependencias: $_" -ForegroundColor Red
    exit 1
}

# 4. Copiar archivos SQL a directorio temporal
Write-Host ""
Write-Host "[4/7] Preparando migración de base de datos..." -ForegroundColor Yellow
$sqlFile = "scripts\migrations\001_add_resilience_fields.sql"
$sqlDir = Split-Path $sqlFile -Parent

if (-not (Test-Path $sqlDir)) {
    New-Item -ItemType Directory -Path $sqlDir -Force | Out-Null
}

# Aquí deberías copiar el contenido del archivo SQL generado
Write-Host "  ⚠️  ACCIÓN MANUAL REQUERIDA:" -ForegroundColor Yellow
Write-Host "     1. Copia el archivo 'migration_001_add_resilience_fields.sql'" -ForegroundColor White
Write-Host "     2. Pégalo en: $sqlFile" -ForegroundColor White
Write-Host "     3. Ejecuta: docker cp ""$sqlFile"" neural_bookmark_postgres:/tmp/migration.sql" -ForegroundColor White
Write-Host "     4. Ejecuta: docker-compose exec postgres psql -U bookmark_user -d neural_bookmarks -f /tmp/migration.sql" -ForegroundColor White

# 5. Aplicar cambios de código
Write-Host ""
Write-Host "[5/7] Aplicando cambios de código..." -ForegroundColor Yellow

Write-Host "  ⚠️  ACCIÓN MANUAL REQUERIDA:" -ForegroundColor Yellow
Write-Host "     Reemplaza estos archivos:" -ForegroundColor White
Write-Host "     - app\models.py → models_updated.py" -ForegroundColor White
Write-Host "     - app\services\scraper.py → scraper_resilient.py" -ForegroundColor White
Write-Host "     - app\agents.py → agents_resilient.py" -ForegroundColor White

# 6. Verificar instalación
Write-Host ""
Write-Host "[6/7] Verificando instalación..." -ForegroundColor Yellow

$checks = @()

# Check tenacity
try {
    python -c "import tenacity; print('OK')" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ tenacity instalado" -ForegroundColor Green
        $checks += $true
    } else {
        throw
    }
} catch {
    Write-Host "  ❌ tenacity NO instalado" -ForegroundColor Red
    $checks += $false
}

# Check fake_useragent
try {
    python -c "import fake_useragent; print('OK')" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ fake_useragent instalado" -ForegroundColor Green
        $checks += $true
    } else {
        throw
    }
} catch {
    Write-Host "  ❌ fake_useragent NO instalado" -ForegroundColor Red
    $checks += $false
}

# 7. Resumen
Write-Host ""
Write-Host "[7/7] Resumen de instalación" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────" -ForegroundColor Gray

$successCount = ($checks | Where-Object { $_ -eq $true }).Count
$totalChecks = $checks.Count

Write-Host ""
Write-Host "Verificaciones: $successCount/$totalChecks pasadas" -ForegroundColor $(if ($successCount -eq $totalChecks) { "Green" } else { "Yellow" })
Write-Host "Backup creado en: $BackupDir" -ForegroundColor Cyan

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  PRÓXIMOS PASOS:" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Ejecutar migración SQL (ver instrucciones arriba)" -ForegroundColor White
Write-Host "2. Reemplazar archivos Python (ver lista arriba)" -ForegroundColor White
Write-Host "3. Reiniciar containers:" -ForegroundColor White
Write-Host "   docker-compose restart api" -ForegroundColor Cyan
Write-Host "4. Probar con smoke test:" -ForegroundColor White
Write-Host "   .\tests\manual\smoke_test.ps1" -ForegroundColor Cyan
Write-Host ""

if ($successCount -lt $totalChecks) {
    Write-Host "⚠️  ADVERTENCIA: Algunas verificaciones fallaron" -ForegroundColor Yellow
    Write-Host "   Revisa los errores arriba antes de continuar" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Sprint 1 listo para aplicar!" -ForegroundColor Green
Write-Host ""