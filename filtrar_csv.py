# guarda como filtrar_csv.py
import csv

# 1. Cargar URLs a borrar
with open('urls_para_borrar.txt', 'r') as f:
    urls_muertas = {line.strip() for line in f if line.strip()}

print(f"URLs detectadas para eliminar: {len(urls_muertas)}")

# 2. Filtrar el CSV
try:
    with open('bookmarks.csv', 'r', encoding='utf-8') as f_in, \
         open('bookmarks_limpio.csv', 'w', encoding='utf-8', newline='') as f_out:
        
        reader = csv.reader(f_in)
        writer = csv.writer(f_out)
        
        eliminados = 0
        for row in reader:
            # Si alguna de las URLs muertas está en esta fila, la saltamos
            if any(url in "".join(row) for url in urls_muertas):
                eliminados += 1
                continue
            writer.writerow(row)
            
    print(f"✅ Proceso terminado.")
    print(f"Filas eliminadas del CSV: {eliminados}")
    print(f"Nuevo archivo creado: bookmarks_limpio.csv")

except FileNotFoundError:
    print("❌ Error: No se encontró 'bookmarks.csv'")