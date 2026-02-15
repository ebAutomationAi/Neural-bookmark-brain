import os
from pathlib import Path

# Configuración
SALIDA = "contexto_auditoria_wsl.txt"
IGNORAR_DIRS = ['.git', '__pycache__', 'node_modules', 'venv', '.idea', 'dist', 'build']
IGNORAR_EXTENSIONES = ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.log', '.ico', '.md', '.txt', '.svg', '.woff', '.woff2', '.ttf', '.eot', '.zip', '.tar', '.gz', '.exe', '.dll', '.so', '.dylib']

def generar_contexto():
    root = Path('.')
    ignorar_dirs_lower = {d.lower() for d in IGNORAR_DIRS}
    ignorar_ext_lower = {e.lower() for e in IGNORAR_EXTENSIONES}

    # Primera pasada: recopilar archivos
    archivos_validos = []
    for path in root.rglob('*'):
        # Filtros
        if not path.is_file(): continue
        if any(part.lower() in ignorar_dirs_lower for part in path.parts): continue

        # Evitar incluir el archivo de salida y este script
        if path.name == "recopila_codigos_wsl.py": continue
        if path.name == SALIDA: continue

        # Excluir archivos binarios
        if path.suffix.lower() in ignorar_ext_lower: continue

        # Incluir todos los archivos
        archivos_validos.append(path)

    # Ordenar archivos por ruta
    archivos_validos.sort()

    # Segunda pasada: escribir con tabla de contenidos
    with open(SALIDA, 'w', encoding='utf-8') as outfile:
        outfile.write("# AUDIT CONTEXT - BOOKMARKS SYSTEM\n\n")
        
        # Tabla de contenidos
        outfile.write("## TABLA DE CONTENIDOS\n\n")
        for idx, path in enumerate(archivos_validos, 1):
            rel_path = path.relative_to(root)
            outfile.write(f"{idx}. {rel_path}\n")
        outfile.write(f"\nTotal de archivos: {len(archivos_validos)}\n\n")
        outfile.write(f"{'='*80}\n\n")
        
        # Contenido de archivos
        for path in archivos_validos:
            try:
                rel_path = path.relative_to(root)
                content = path.read_text(encoding='utf-8', errors='ignore')
                
                outfile.write(f"{'='*50}\n")
                outfile.write(f"FILE PATH: {rel_path}\n")
                outfile.write(f"{'='*50}\n")
                outfile.write(content + "\n\n")
                print(f"✅ Agregado: {rel_path}")
            except Exception as e:
                print(f"❌ Error leyendo {path}: {e}")

    print(f"\n✨ ¡Listo! Sube el archivo '{SALIDA}' a la Knowledge Base del chat para que el modelo pueda acceder a este contexto de auditoría.")
    print(f"📊 Total: {len(archivos_validos)} archivos procesados")

if __name__ == "__main__":
    generar_contexto()
