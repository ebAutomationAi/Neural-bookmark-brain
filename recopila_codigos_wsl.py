import os
import re
from pathlib import Path
from typing import List, Tuple, Dict

# Configuración
SALIDA = "contexto_auditoria_wsl.txt"
MAX_FILE_SIZE = 100 * 1024  # 100 KB máximo por archivo
MAX_TOTAL_SIZE = 10 * 1024 * 1024  # 10 MB total

# Directorios a ignorar (case-insensitive)
IGNORAR_DIRS = {
    '.git', '__pycache__', 'node_modules', 'venv', '.idea', 
    'dist', 'build', '.mypy_cache', '.pytest_cache', '.vscode',
    'htmlcov', '.coverage', 'test-results', '__pycache__', 
    '.env', '.env.local', '.env.*'
}

# Extensiones de código FUENTE a incluir (positivo)
EXTENSIONES_CODIGO = {
    '.py', '.pyi', '.pyx', '.pxd', '.c', '.cpp', '.h', '.hpp',
    '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
    '.sql', '.html', '.css', '.scss', '.sass', '.vue',
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf'
}

# Archivos específicos IMPORTANTES a incluir siempre
ARCHIVOS_ESENCIALES = {
    'requirements.txt', 'requirements-dev.txt', 'pyproject.toml',
    'setup.py', 'setup.cfg', 'Pipfile', 'Pipfile.lock',
    'package.json', 'package-lock.json', 'yarn.lock',
    '.env.example', 'Dockerfile', 'docker-compose.yml',
    'README.md', 'CONTRIBUTING.md', 'LICENSE',
    'pytest.ini', 'pyrightconfig.json', 'tsconfig.json',
    'Makefile', 'manage.py', 'wsgi.py', 'asgi.py'
}

# ============================================================================
# 🔐 PATRONES DE DATOS SENSIBLES A ENMASCARAR
# ============================================================================
PATRONES_SENSIBLES: List[Tuple[str, str]] = [
    # API Keys
    (r'(?i)(api[_-]?key|apikey)["\s]*[:=]["\s]*([a-zA-Z0-9\-_]{20,})', r'\1: "xxxxxxxxxx"'),
    (r'(?i)(secret[_-]?key|secretkey)["\s]*[:=]["\s]*([a-zA-Z0-9\-_]{20,})', r'\1: "xxxxxxxxxx"'),
    (r'(?i)(access[_-]?token|accesstoken)["\s]*[:=]["\s]*([a-zA-Z0-9\-_\.]{20,})', r'\1: "xxxxxxxxxx"'),
    (r'(?i)(refresh[_-]?token|refreshtoken)["\s]*[:=]["\s]*([a-zA-Z0-9\-_\.]{20,})', r'\1: "xxxxxxxxxx"'),
    
    # Contraseñas
    (r'(?i)(password|passwd|pwd)["\s]*[:=]["\s]*([^"\n]+)', r'\1: "xxxxxxxxxx"'),
    (r'(?i)(contraseña|contrasena)["\s]*[:=]["\s]*([^"\n]+)', r'\1: "xxxxxxxxxx"'),
    
    # Tokens específicos
    (r'(?i)(openai[_-]?key|openai[_-]?api[_-]?key)["\s]*[:=]["\s]*([a-zA-Z0-9\-_]{20,})', r'\1: "xxxxxxxxxx"'),
    (r'(?i)(anthropic[_-]?key|anthropic[_-]?api[_-]?key)["\s]*[:=]["\s]*([a-zA-Z0-9\-_]{20,})', r'\1: "xxxxxxxxxx"'),
    (r'(?i)(huggingface[_-]?key|huggingface[_-]?api[_-]?key|hf[_-]?token)["\s]*[:=]["\s]*([a-zA-Z0-9\-_]{20,})', r'\1: "xxxxxxxxxx"'),
    (r'(?i)(claude[_-]?key|claude[_-]?api[_-]?key)["\s]*[:=]["\s]*([a-zA-Z0-9\-_]{20,})', r'\1: "xxxxxxxxxx"'),
    
    # URLs con credenciales
    (r'https?://[^:]+:([^@]+)@', r'https://user:xxxxxxxxxx@'),
    
    # JWT Tokens
    (r'(?i)(bearer|token)["\s]*[:=]["\s]*([a-zA-Z0-9\-_\.]{100,})', r'\1: "xxxxxxxxxx"'),
    (r'eyJ[a-zA-Z0-9\-_\.]{100,}', 'xxxxxxxxxx'),
    
    # AWS
    (r'(?i)aws[_-]?access[_-]?key[_-]?id["\s]*[:=]["\s]*([a-zA-Z0-9]{20})', r'\1: "xxxxxxxxxx"'),
    (r'(?i)aws[_-]?secret[_-]?access[_-]?key["\s]*[:=]["\s]*([a-zA-Z0-9\/\+]{40})', r'\1: "xxxxxxxxxx"'),
    
    # Database
    (r'(?i)(database[_-]?url|db[_-]?url)["\s]*[:=]["\s]*([^"\n]+://[^:]+:)([^@]+)(@)', r'\1: "\2xxxxxxxxxx\4'),
    
    # Email passwords
    (r'(?i)(smtp[_-]?password|email[_-]?password)["\s]*[:=]["\s]*([^"\n]+)', r'\1: "xxxxxxxxxx"'),
    
    # SSH Keys (en archivos de texto)
    (r'-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----.*?-----END \1 PRIVATE KEY-----', '-----BEGIN PRIVATE KEY-----\nxxxxxxxxxx\n-----END PRIVATE KEY-----'),
    
    # Números de tarjetas de crédito (patrón básico)
    (r'\b(?:\d{4}[-\s]?){3}\d{4}\b', 'xxxx-xxxx-xxxx-xxxx'),
    
    # Números de teléfono (patrón básico)
    (r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', 'xxxxxxxxxx'),
    
    # Variables de entorno sensibles en .env
    (r'(?i)^([A-Z_]*SECRET[A-Z_]*)=(.+)$', r'\1=xxxxxxxxxx'),
    (r'(?i)^([A-Z_]*PASSWORD[A-Z_]*)=(.+)$', r'\1=xxxxxxxxxx'),
    (r'(?i)^([A-Z_]*TOKEN[A-Z_]*)=(.+)$', r'\1=xxxxxxxxxx'),
    (r'(?i)^([A-Z_]*KEY[A-Z_]*)=(.+)$', r'\1=xxxxxxxxxx'),
]

def enmascarar_datos_sensibles(content: str, filepath: str) -> Tuple[str, List[str]]:
    """
    Enmascara datos sensibles en el contenido usando regex patterns.
    Devuelve el contenido limpio y una lista de advertencias.
    """
    advertencias = []
    contenido_modificado = content
    
    for patron, reemplazo in PATRONES_SENSIBLES:
        matches = re.findall(patron, contenido_modificado, re.MULTILINE | re.DOTALL)
        if matches:
            tipo_dato = patron.split('[')[0] if '[' in patron else 'sensible'
            advertencias.append(f"  ⚠️  Encontrado {len(matches)} coincidencia(s) de tipo: {tipo_dato}")
            contenido_modificado = re.sub(patron, reemplazo, contenido_modificado, flags=re.MULTILINE | re.DOTALL)
    
    return contenido_modificado, advertencias

def es_archivo_codigo(path: Path) -> bool:
    """Determina si un archivo es relevante para el contexto"""
    name = path.name.lower()
    
    # Siempre incluir archivos esenciales
    if name in ARCHIVOS_ESENCIALES:
        return True
    
    # Incluir por extensión
    if path.suffix.lower() in EXTENSIONES_CODIGO:
        return True
    
    return False

def generar_contexto():
    root = Path('.')
    ignorar_dirs_lower = {d.lower() for d in IGNORAR_DIRS}
    
    print("🔍 Escaneando proyecto...")
    
    # Recopilar archivos
    archivos_validos = []
    
    for path in sorted(root.rglob('*')):
        try:
            # Saltar si no es archivo
            if not path.is_file():
                continue
            
            # Saltar directorios ignorados
            if any(part.lower() in ignorar_dirs_lower for part in path.parts):
                continue
            
            # Saltar el script actual y salida
            if path.name in ["recopila_codigos_wsl.py", SALIDA]:
                continue
            
            # Verificar si es archivo de código relevante
            if not es_archivo_codigo(path):
                continue
            
            # Verificar tamaño
            if path.stat().st_size > MAX_FILE_SIZE:
                print(f"⚠️  Saltado (demasiado grande): {path.relative_to(root)} ({path.stat().st_size / 1024:.1f} KB)")
                continue
            
            archivos_validos.append(path)
            
        except Exception as e:
            print(f"❌ Error procesando {path}: {e}")
    
    print(f"✅ Encontrados {len(archivos_validos)} archivos relevantes")
    
    # Escribir contexto
    total_size = 0
    archivos_procesados = 0
    total_enmascarados = 0
    
    with open(SALIDA, 'w', encoding='utf-8') as outfile:
        # Encabezado de seguridad
        outfile.write("="*80 + "\n")
        outfile.write("🔒 AUDIT CONTEXT - BOOKMARKS SYSTEM (DATOS SENSIBLES ENMASCARADOS)\n")
        outfile.write("="*80 + "\n\n")
        outfile.write("⚠️  ADVERTENCIA DE SEGURIDAD:\n")
        outfile.write("   Todos los datos sensibles (API keys, passwords, tokens, etc.)\n")
        outfile.write("   han sido automáticamente enmascarados con 'xxxxxxxxxx'\n")
        outfile.write("   para proteger la información confidencial del proyecto.\n\n")
        
        # Resumen ejecutivo
        outfile.write("## 📋 RESUMEN EJECUTIVO\n\n")
        outfile.write("**Tipo de Proyecto:** Sistema de Bookmarks con Scraping y API\n")
        outfile.write("**Tecnologías Principales:**\n")
        outfile.write("- Backend: FastAPI, Python 3.12\n")
        outfile.write("- Base de Datos: PostgreSQL (asyncpg, SQLAlchemy)\n")
        outfile.write("- Scraping: Trafilatura, Courlan, Fake UserAgent\n")
        outfile.write("- ML/AI: Transformers, Torch, Scikit-learn\n")
        outfile.write("- Frontend: React, TypeScript, Vite\n")
        outfile.write("- Testing: Pytest, Pytest-asyncio\n")
        outfile.write("- Validación: Pydantic v2\n\n")
        
        # Estructura de directorios
        outfile.write("## 📂 ESTRUCTURA DE DIRECTORIOS\n\n")
        outfile.write("```\n")
        for item in sorted(root.iterdir()):
            if item.name not in IGNORAR_DIRS and not item.name.startswith('.'):
                if item.is_dir():
                    outfile.write(f"{item.name}/\n")
                else:
                    outfile.write(f"{item.name}\n")
        outfile.write("```\n\n")
        
        # Tabla de contenidos
        outfile.write("## 📖 TABLA DE CONTENIDOS\n\n")
        for idx, path in enumerate(archivos_validos, 1):
            rel_path = path.relative_to(root)
            outfile.write(f"{idx}. `{rel_path}`\n")
        outfile.write(f"\n**Total de archivos:** {len(archivos_validos)}\n\n")
        outfile.write("="*80 + "\n\n")
        
        # Contenido de archivos
        for path in archivos_validos:
            if total_size > MAX_TOTAL_SIZE:
                outfile.write(f"\n⚠️  LÍMITE DE TAMAÑO ALCANZADO. Archivos restantes omitidos.\n")
                break
            
            try:
                rel_path = path.relative_to(root)
                
                # Leer contenido original
                content = path.read_text(encoding='utf-8', errors='replace')
                
                # Enmascarar datos sensibles
                content_limpio, advertencias = enmascarar_datos_sensibles(content, str(rel_path))
                
                if advertencias:
                    total_enmascarados += 1
                    print(f"🔒 [{archivos_procesados+1}/{len(archivos_validos)}] {rel_path} - {len(advertencias)} dato(s) enmascarado(s)")
                else:
                    print(f"✅ [{archivos_procesados+1}/{len(archivos_validos)}] {rel_path}")
                
                file_size = len(content_limpio.encode('utf-8'))
                total_size += file_size
                archivos_procesados += 1
                
                # Escribir al archivo
                outfile.write(f"\n{'='*80}\n")
                outfile.write(f"📄 ARCHIVO: {rel_path}\n")
                outfile.write(f"📏 Tamaño: {file_size / 1024:.1f} KB\n")
                
                if advertencias:
                    outfile.write(f"⚠️  DATOS SENSIBLES ENMASCARADOS:\n")
                    for adv in advertencias:
                        outfile.write(f"{adv}\n")
                
                outfile.write(f"{'='*80}\n\n")
                outfile.write(content_limpio)
                outfile.write("\n\n")
                
            except Exception as e:
                print(f"❌ Error leyendo {path}: {e}")
                outfile.write(f"\n⚠️  Error al leer {rel_path}: {e}\n\n")
    
    # Resumen final
    print(f"\n" + "="*60)
    print(f"✨ ¡COMPLETADO!")
    print(f"📊 Archivos procesados: {archivos_procesados}/{len(archivos_validos)}")
    print(f"🔒 Archivos con datos enmascarados: {total_enmascarados}")
    print(f"💾 Tamaño total: {total_size / 1024 / 1024:.2f} MB")
    print(f"📄 Archivo generado: '{SALIDA}'")
    print("="*60)
    
    if total_enmascarados > 0:
        print(f"\n⚠️  ADVERTENCIA: Se enmascararon datos sensibles en {total_enmascarados} archivo(s)")
        print(f"   Revisa el archivo '{SALIDA}' para verificar qué fue ocultado.")
    
    print(f"\n💡 Consejo: Sube '{SALIDA}' a la Knowledge Base para que Claude 4.5")
    print(f"   tenga contexto completo del proyecto Bookmarks System.")
    print(f"   ✅ Todos los datos sensibles han sido protegidos.")

if __name__ == "__main__":
    generar_contexto()