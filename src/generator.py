"""Generación entera reproducible sin alterar random global."""
import random
from src.validation import validar_entrada

def generar_instancia(n_archivos: int, capacidad: int, semilla: int = 42, familia='uniforme') -> list:
    validar_entrada([], capacidad)
    if isinstance(n_archivos, bool) or not isinstance(n_archivos, int) or n_archivos < 0:
        raise ValueError('n_archivos debe ser entero no negativo.')
    if not isinstance(capacidad, int):
        raise ValueError('La generación requiere capacidad entera.')
    rangos = {'uniforme': (1, capacidad), 'pequenos': (1, max(1, capacidad // 4)),
              'grandes': (capacidad // 2 + 1, capacidad)}
    if familia not in rangos:
        raise ValueError('Familia desconocida.')
    rng = random.Random(semilla)
    return [rng.randint(*rangos[familia]) for _ in range(n_archivos)]
