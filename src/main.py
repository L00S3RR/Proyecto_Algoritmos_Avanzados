"""Prototipo mínimo ejecutable del proyecto de Bin Packing 1D.

Permite definir una instancia, ejecutar algoritmos y producir una salida verificable.
"""

import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.algorithms.approximate import first_fit_decreasing, best_fit_decreasing
from src.algorithms.exact import bin_packing_exacto
from src.generator import generar_instancia

def main():
    print("=" * 60)
    print("PROTOTIPO: Bin Packing 1D - Asignación de archivos a discos")
    print("=" * 60)

    # 1. Definir o cargar una instancia
    print("\n[1] Definiendo instancia de prueba...")
    
    # Opción A: Instancia manual (ejemplo conocido)
    archivos_manual = [4, 3, 2.5, 2, 1.5, 1]
    capacidad_manual = 5
    
    # Opción B: Instancia generada (reproducible)
    archivos_generados = generar_instancia(10, 10, semilla=42)
    capacidad_generada = 10

    print(f"  Instancia manual: {archivos_manual} GB, Capacidad: {capacidad_manual} GB/disco")
    print(f"  Instancia generada: {archivos_generados} (MB), Capacidad: {capacidad_generada} (MB)/disco")

    # 2. Ejecutar algoritmo básico (First Fit Decreasing)
    print("\n[2] Ejecutando algoritmo: First Fit Decreasing (FFD)...")
    solucion_ffd = first_fit_decreasing(archivos_manual, capacidad_manual)

    print("\n  Solución FFD:")
    for i, disco in enumerate(solucion_ffd):
        print(f"    Disco {i+1}: {disco} = {sum(disco)}/{capacidad_manual} GB")
    print(f"  Total de discos: {len(solucion_ffd)}")

    # 3. Ejecutar algoritmo exacto
    print("\n[3] Ejecutando algoritmo exacto (búsqueda exhaustiva)...")
    solucion_exacta = bin_packing_exacto(archivos_manual, capacidad_manual)

    print("\n  Solución exacta:")
    for i, disco in enumerate(solucion_exacta):
        print(f"    Disco {i+1}: {disco} = {sum(disco)}/{capacidad_manual} GB")
    print(f"  Total de discos: {len(solucion_exacta)}")

    # 4. Ejecutar BFD
    print("\n[4] Ejecutando algoritmo: Best Fit Decreasing (BFD)...")
    solucion_bfd = best_fit_decreasing(archivos_manual, capacidad_manual)

    print("\n  Solución BFD:")
    for i, disco in enumerate(solucion_bfd):
        print(f"    Disco {i+1}: {disco} = {sum(disco)}/{capacidad_manual} GB")
    print(f"  Total de discos: {len(solucion_bfd)}")

    # 5. Validación de la salida
    print("\n[5] Validación de la salida...")
    
    valido = True
    # Verificar que todos los archivos están asignados
    archivos_asignados = []
    for disco in solucion_ffd:
        archivos_asignados.extend(disco)
    
    if sorted(archivos_asignados) != sorted(archivos_manual):
        print("  [ERROR] No todos los archivos fueron asignados.")
        valido = False
    else:
        print("  [OK] Todos los archivos asignados.")

    # Verificar que ninguna capacidad excede el límite
    for i, disco in enumerate(solucion_ffd):
        if sum(disco) > capacidad_manual:
            print(f"  [ERROR] Disco {i+1} excede capacidad.")
            valido = False
        else:
            print(f"  [OK] Disco {i+1} dentro de capacidad.")

    if valido:
        print("\n  ¡PROTOTIPO EJECUTADO EXITOSAMENTE!")
    else:
        print("\n  ¡ERRORES EN LA EJECUCIÓN!")

    print("\n" + "=" * 60)
    print("DEMOSTRACIÓN COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    main()
