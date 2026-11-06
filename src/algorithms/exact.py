"""Búsqueda exacta con poda por incumbente y simetría."""
from time import perf_counter
from src.algorithms.approximate import first_fit_decreasing
from src.validation import validar_entrada

def bin_packing_exacto(archivos: list, capacidad: int, limite_segundos=None) -> list:
    """Devuelve el óptimo o lanza TimeoutError si no logra certificarlo."""
    validar_entrada(archivos, capacidad)
    if limite_segundos is not None and limite_segundos <= 0:
        raise ValueError('El límite debe ser positivo.')
    orden = sorted(archivos, reverse=True)
    mejor = first_fit_decreasing(orden, capacidad)
    discos, cargas = [], []
    inicio = perf_counter()
    def buscar(idx):
        nonlocal mejor
        if limite_segundos is not None and perf_counter() - inicio >= limite_segundos:
            raise TimeoutError('No se certificó el óptimo dentro del límite.')
        if idx == len(orden):
            if len(discos) < len(mejor):
                mejor = [d[:] for d in discos]
            return
        if len(discos) >= len(mejor):
            return
        archivo = orden[idx]
        vistas = set()
        for i in range(len(discos)):
            if cargas[i] in vistas:
                continue
            vistas.add(cargas[i])
            if cargas[i] + archivo <= capacidad:
                anterior = cargas[i]
                discos[i].append(archivo)
                cargas[i] += archivo
                buscar(idx + 1)
                cargas[i] = anterior
                discos[i].pop()
        if len(discos) + 1 < len(mejor):
            discos.append([archivo])
            cargas.append(archivo)
            buscar(idx + 1)
            cargas.pop()
            discos.pop()
    buscar(0)
    return mejor
