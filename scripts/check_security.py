#!/usr/bin/env python3
"""
Script para verificar la seguridad del proyecto
"""
import os
import sys
import subprocess
from pathlib import Path

root_dir = Path(__file__).parent.parent


def check_env_in_gitignore():
    """Verifica que .env está en .gitignore"""
    print("🔒 Verificando que .env está protegido...")
    
    gitignore_path = root_dir / ".gitignore"
    
    if not gitignore_path.exists():
        print("   ❌ No existe archivo .gitignore")
        return False
    
    with open(gitignore_path) as f:
        content = f.read()
    
    if ".env" in content:
        print("   ✅ .env está en .gitignore")
        
        # Verificar con git
        try:
            result = subprocess.run(
                ["git", "check-ignore", "-v", ".env"],
                cwd=root_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"   ✅ Git confirma que .env está ignorado:")
                print(f"      {result.stdout.strip()}")
                return True
            else:
                print("   ⚠️  Git no confirma que .env esté ignorado")
                print("      (Esto puede ser normal si no es un repo git)")
                return True
        except FileNotFoundError:
            print("   ⚠️  Git no está instalado (verificación manual)")
            return True
    else:
        print("   ❌ .env NO está en .gitignore")
        print("   💡 Añade '.env' al archivo .gitignore")
        return False


def check_env_not_committed():
    """Verifica que .env no está en el repositorio"""
    print("\n📂 Verificando que .env no está en git...")
    
    try:
        # Verificar si .env está trackeado por git
        result = subprocess.run(
            ["git", "ls-files", ".env"],
            cwd=root_dir,
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            print("   ❌ PELIGRO: .env está committeado en git!")
            print("   🚨 Tu archivo .env con secretos está en el repositorio")
            print("\n   💡 Para removerlo:")
            print("      git rm --cached .env")
            print("      git commit -m 'Remove .env from git'")
            return False
        else:
            print("   ✅ .env no está committeado (correcto)")
            return True
    
    except FileNotFoundError:
        print("   ⚠️  Git no está instalado (no se puede verificar)")
        return True
    except subprocess.CalledProcessError:
        print("   ⚠️  No es un repositorio git")
        return True


def check_env_example_exists():
    """Verifica que existe .env.example"""
    print("\n📝 Verificando .env.example...")
    
    env_example = root_dir / ".env.example"
    
    if env_example.exists():
        print("   ✅ .env.example existe")
        
        # Verificar que no tenga valores reales
        with open(env_example) as f:
            content = f.read()
        
        dangerous_patterns = [
            "gsk_",  # Groq API keys empiezan con gsk_
            "sk-",   # OpenAI keys empiezan con sk-
            "postgresql://.*:.*@",  # URLs de DB con passwords reales
        ]
        
        import re
        has_secrets = False
        for pattern in dangerous_patterns:
            if re.search(pattern, content):
                print(f"   ⚠️  .env.example podría contener secretos reales (patrón: {pattern})")
                has_secrets = True
        
        if not has_secrets:
            print("   ✅ .env.example no parece contener secretos reales")
        
        return True
    else:
        print("   ⚠️  .env.example no existe")
        print("      Considera crear uno como template")
        return False


def check_env_variables_in_code():
    """Verifica que no hay secretos hardcodeados en el código"""
    print("\n🔍 Buscando secretos hardcodeados en el código...")
    
    dangerous_patterns = {
        "API key hardcoded": r'api[_-]?key\s*=\s*["\'][a-zA-Z0-9]{20,}["\']',
        "Password hardcoded": r'password\s*=\s*["\'][^"\']{8,}["\']',
        "Groq key": r'gsk_[a-zA-Z0-9]{40,}',
        "Database URL with password": r'postgresql://[^:]+:[^@]+@',
    }
    
    found_issues = False
    
    for py_file in root_dir.rglob("*.py"):
        # Ignorar tests y venv
        if "venv" in str(py_file) or "test" in str(py_file):
            continue
        
        try:
            with open(py_file) as f:
                content = f.read()
            
            for name, pattern in dangerous_patterns.items():
                import re
                if re.search(pattern, content, re.IGNORECASE):
                    print(f"   ⚠️  Posible {name} en: {py_file.relative_to(root_dir)}")
                    found_issues = True
        except:
            pass
    
    if not found_issues:
        print("   ✅ No se encontraron secretos hardcodeados obvios")
        return True
    else:
        print("   ⚠️  Se encontraron posibles secretos - revisar manualmente")
        return False


def check_rate_limiting_enabled():
    """Verifica que el rate limiting está habilitado"""
    print("\n🚦 Verificando rate limiting...")
    
    env_file = root_dir / ".env"
    
    if not env_file.exists():
        print("   ⚠️  .env no existe")
        return False
    
    with open(env_file) as f:
        content = f.read()
    
    if "RATE_LIMIT_ENABLED=true" in content or "RATE_LIMIT_ENABLED" not in content:
        print("   ✅ Rate limiting está habilitado")
        
        # Verificar límites configurados
        if "RATE_LIMIT_SEARCH" in content:
            print("   ✅ Límites de búsqueda configurados")
        if "RATE_LIMIT_CREATE" in content:
            print("   ✅ Límites de creación configurados")
        
        return True
    else:
        print("   ⚠️  Rate limiting parece estar deshabilitado")
        print("      Considera habilitarlo en producción")
        return False


def main():
    """Función principal"""
    print("="*60)
    print("🔐 VERIFICACIÓN DE SEGURIDAD")
    print("="*60)
    
    checks = []
    
    # 1. .env en .gitignore
    checks.append(("'.env' en .gitignore", check_env_in_gitignore()))
    
    # 2. .env no committeado
    checks.append(("'.env' no committeado", check_env_not_committed()))
    
    # 3. .env.example existe
    checks.append((".env.example existe", check_env_example_exists()))
    
    # 4. No secretos hardcodeados
    checks.append(("No secretos hardcoded", check_env_variables_in_code()))
    
    # 5. Rate limiting
    checks.append(("Rate limiting habilitado", check_rate_limiting_enabled()))
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE SEGURIDAD")
    print("="*60)
    
    for name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} - {name}")
    
    print("="*60)
    
    all_passed = all(check[1] for check in checks)
    critical_passed = checks[0][1] and checks[1][1]  # .gitignore y no committeado
    
    if all_passed:
        print("\n✅ Todas las verificaciones de seguridad pasaron!")
        return 0
    elif critical_passed:
        print("\n⚠️  Algunas verificaciones fallaron, pero las críticas pasaron")
        print("   Tu .env está protegido, revisa las advertencias arriba")
        return 0
    else:
        print("\n🚨 VERIFICACIONES CRÍTICAS FALLARON!")
        print("   Tu archivo .env podría estar expuesto")
        print("   Revisa y corrige los errores inmediatamente")
        return 1


if __name__ == "__main__":
    sys.exit(main())
