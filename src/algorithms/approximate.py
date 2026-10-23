"""Algoritmos de aproximacion FFD y BFD para bin packing 1D."""
from src.validation import normalize_instance


def first_fit_decreasing(archivos: list, capacidad: float) -> list:
    """FFD: ordena de mayor a menor y usa el primer disco con espacio suficiente."""
    items, cap = normalize_instance(archivos, capacidad)
    items.sort(key=lambda item: item[1], reverse=True)
    discos, restantes = [], []
    for archivo, tamano in items:
        for i, espacio in enumerate(restantes):
            if tamano <= espacio:
                discos[i].append(archivo)
                restantes[i] -= tamano
                break
        else:
            discos.append([archivo])
            restantes.append(cap - tamano)
    return discos


def best_fit_decreasing(archivos: list, capacidad: float) -> list:
    """BFD: ordena de mayor a menor y elige el disco que deja menos espacio libre."""
    items, cap = normalize_instance(archivos, capacidad)
    items.sort(key=lambda item: item[1], reverse=True)
    discos, restantes = [], []
    for archivo, tamano in items:
        candidatos = [(espacio, i) for i, espacio in enumerate(restantes) if espacio >= tamano]
        if candidatos:
            _, i = min(candidatos)
            discos[i].append(archivo)
            restantes[i] -= tamano
        else:
            discos.append([archivo])
            restantes.append(cap - tamano)
    return discos
