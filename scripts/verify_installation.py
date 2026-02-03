#!/usr/bin/env python3
"""
Script de verificación de instalación y dependencias
"""
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Verifica versión de Python"""
    print("🐍 Verificando Python...")
    version = sys.version_info
    
    if version.major == 3 and version.minor >= 11:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} - Se requiere 3.11+")
        return False


def check_docker():
    """Verifica Docker"""
    print("\n🐳 Verificando Docker...")
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"   ✅ {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   ❌ Docker no encontrado")
        return False


def check_docker_compose():
    """Verifica Docker Compose"""
    print("\n🐳 Verificando Docker Compose...")
    try:
        result = subprocess.run(
            ["docker-compose", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"   ✅ {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   ❌ Docker Compose no encontrado")
        return False


def check_env_file():
    """Verifica archivo .env"""
    print("\n⚙️  Verificando configuración...")
    env_file = Path(".env")
    
    if env_file.exists():
        print("   ✅ Archivo .env encontrado")
        
        # Verificar GROQ_API_KEY
        with open(env_file) as f:
            content = f.read()
            if "GROQ_API_KEY=your_groq_api_key_here" in content:
                print("   ⚠️  ADVERTENCIA: GROQ_API_KEY no configurada")
                print("      Edita .env y añade tu API key de Groq")
                return False
            elif "GROQ_API_KEY=" in content:
                print("   ✅ GROQ_API_KEY configurada")
                return True
    else:
        print("   ❌ Archivo .env no encontrado")
        print("      Copia .env.example a .env y configura las variables")
        return False


def check_data_directory():
    """Verifica directorio de datos"""
    print("\n📁 Verificando directorio de datos...")
    data_dir = Path("data")
    
    if data_dir.exists():
        print("   ✅ Directorio data/ existe")
        
        # Buscar archivos CSV
        csv_files = list(data_dir.glob("*.csv"))
        if csv_files:
            print(f"   ℹ️  {len(csv_files)} archivo(s) CSV encontrado(s):")
            for csv_file in csv_files[:5]:
                print(f"      - {csv_file.name}")
        else:
            print("   ℹ️  No hay archivos CSV en data/")
            print("      Copia tu bookmarks.csv a data/ para importar")
        
        return True
    else:
        print("   ⚠️  Directorio data/ no existe")
        data_dir.mkdir()
        print("   ✅ Directorio data/ creado")
        return True


def check_requirements():
    """Verifica requirements.txt"""
    print("\n📦 Verificando dependencias...")
    req_file = Path("requirements.txt")
    
    if req_file.exists():
        print("   ✅ requirements.txt encontrado")
        
        # Contar dependencias
        with open(req_file) as f:
            packages = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
        print(f"   ℹ️  {len(packages)} paquetes listados")
        return True
    else:
        print("   ❌ requirements.txt no encontrado")
        return False


def main():
    """Verificación principal"""
    print("=" * 60)
    print("🧠 Neural Bookmark Brain - Verificación de Instalación")
    print("=" * 60)
    
    checks = {
        "Python 3.11+": check_python_version(),
        "Docker": check_docker(),
        "Docker Compose": check_docker_compose(),
        "Configuración (.env)": check_env_file(),
        "Directorio de datos": check_data_directory(),
        "Dependencias": check_requirements(),
    }
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
    
    all_passed = all(checks.values())
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("✅ ¡Todo listo! Puedes continuar con:")
        print("\n   docker-compose up -d")
        print("   make import-csv FILE=data/bookmarks.csv")
        print("\n   O consulta el README.md para más información")
    else:
        print("⚠️  Algunas verificaciones fallaron")
        print("   Revisa los errores arriba y corrige antes de continuar")
        print("   Consulta README.md para más ayuda")
    
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
