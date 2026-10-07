"""Generador de datos sintéticos para el problema de bin packing 1D."""

import random

def generar_instancia(n_archivos: int, capacidad: int, semilla: int = 42) -> list:
    """Genera una instancia sintética de archivos con tamaños aleatorios.
    
    Args:
        n_archivos: Número de archivos a generar.
        capacidad: Capacidad máxima de cada disco (en MB).
        semilla: Semilla para reproducibilidad.
    
    Returns:
        Lista de tamaños de archivos (en MB).
    """
    random.seed(semilla)
    # Generar tamaños entre 10% y 90% de la capacidad
    return [random.randint(capacidad // 10, capacidad // 2) for _ in range(n_archivos)]

if __name__ == "__main__":
    instancia = generar_instancia(20, 10240, semilla=42)
    print("Instancia generada:")
    print(instancia)
    print(f"Total: {sum(instancia)} MB")
