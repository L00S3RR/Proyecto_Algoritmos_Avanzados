"""Generacion reproducible de instancias enteras para bin packing 1D."""
import random


def generar_instancia(n_archivos: int, capacidad: int, semilla: int = 42) -> list:
    if isinstance(n_archivos, bool) or not isinstance(n_archivos, int) or n_archivos < 0:
        raise ValueError("La cantidad de archivos debe ser un entero no negativo")
    if isinstance(capacidad, bool) or not isinstance(capacidad, int) or capacidad <= 0:
        raise ValueError("La capacidad debe ser un entero positivo")
    rng = random.Random(semilla)
    minimo = max(1, capacidad // 10)
    maximo = max(minimo, capacidad // 2)
    return [rng.randint(minimo, maximo) for _ in range(n_archivos)]


if __name__ == "__main__":
    instancia = generar_instancia(20, 10240, semilla=42)
    print(instancia)
