#!/usr/bin/env python3
"""
Script para verificar que todas las variables de entorno necesarias están configuradas
"""
import os
import sys
from pathlib import Path

# Añadir el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

def check_env_file():
    """Verifica que el archivo .env existe"""
    env_file = root_dir / ".env"
    
    if not env_file.exists():
        print("❌ Error: No se encontró el archivo .env")
        print(f"   Ubicación esperada: {env_file}")
        print("\n💡 Solución:")
        print(f"   cp .env.example .env")
        print("   Luego edita el archivo .env con tus valores\n")
        return False
    
    print("✅ Archivo .env encontrado")
    return True

def check_configuration():
    """Verifica que la configuración se puede cargar"""
    try:
        from app.config import get_settings
        
        print("\n📋 Verificando configuración...")
        settings = get_settings()
        
        print("✅ Configuración cargada correctamente")
        
        # Verificar variables críticas
        print("\n🔑 Variables de entorno críticas:")
        print(f"   • GROQ_API_KEY: {'✅ Configurada' if settings.GROQ_API_KEY else '❌ No configurada'}")
        print(f"   • DATABASE_URL: ✅ Configurada")
        print(f"   • GROQ_MODEL: {settings.GROQ_MODEL}")
        print(f"   • EMBEDDING_MODEL: {settings.EMBEDDING_MODEL}")
        
        return True
        
    except ValueError as e:
        print("\n❌ Error de validación:")
        print(f"   {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ Error cargando configuración: {e}")
        return False

def check_database_connection():
    """Verifica la conexión a la base de datos"""
    try:
        print("\n🗄️  Verificando conexión a base de datos...")
        
        import asyncio
        from sqlalchemy import text
        from app.database import engine
        
        async def test_connection():
            try:
                async with engine.begin() as conn:
                    result = await conn.execute(text("SELECT 1"))
                    await conn.execute(text("SELECT version()"))
                    return True
            except Exception as e:
                print(f"   ❌ Error de conexión: {e}")
                return False
        
        result = asyncio.run(test_connection())
        
        if result:
            print("   ✅ Conexión a PostgreSQL exitosa")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"   ❌ Error verificando base de datos: {e}")
        return False

def main():
    """Función principal"""
    print("="*60)
    print("🔍 VERIFICACIÓN DE CONFIGURACIÓN")
    print("="*60)
    
    checks = []
    
    # 1. Verificar archivo .env
    checks.append(("Archivo .env", check_env_file()))
    
    # 2. Verificar configuración
    if checks[0][1]:  # Solo si .env existe
        checks.append(("Configuración", check_configuration()))
        
        # 3. Verificar base de datos
        if checks[1][1]:  # Solo si configuración es válida
            checks.append(("Base de datos", check_database_connection()))
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN")
    print("="*60)
    
    all_passed = all(check[1] for check in checks)
    
    for name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} - {name}")
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 ¡Todas las verificaciones pasaron!")
        print("   Puedes iniciar la aplicación con: uvicorn app.main:app --reload\n")
        return 0
    else:
        print("\n⚠️  Algunas verificaciones fallaron")
        print("   Revisa los errores arriba y corrígelos antes de continuar\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
