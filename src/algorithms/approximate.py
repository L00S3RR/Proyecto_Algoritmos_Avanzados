"""FFD y BFD con cargas acumuladas y exploración lineal."""
from src.validation import validar_entrada

def _decreasing(archivos, capacidad, best):
    validar_entrada(archivos, capacidad)
    discos, cargas = [], []
    for archivo in sorted(archivos, reverse=True):
        elegido = None
        for i, carga in enumerate(cargas):
            if carga + archivo <= capacidad:
                if elegido is None or carga > cargas[elegido]:
                    elegido = i
                if not best:
                    break
        if elegido is None:
            discos.append([archivo])
            cargas.append(archivo)
        else:
            discos[elegido].append(archivo)
            cargas[elegido] += archivo
    return discos

def first_fit_decreasing(archivos: list, capacidad: int) -> list:
    return _decreasing(archivos, capacidad, False)

def best_fit_decreasing(archivos: list, capacidad: int) -> list:
    return _decreasing(archivos, capacidad, True)
