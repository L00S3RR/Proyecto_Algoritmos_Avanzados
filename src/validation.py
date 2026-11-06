"""Validación compartida de instancias y soluciones."""
from collections import Counter
from math import isfinite, fsum
from numbers import Real

def validar_entrada(archivos, capacidad):
    if isinstance(capacidad, bool) or not isinstance(capacidad, Real) or not isfinite(capacidad) or capacidad <= 0:
        raise ValueError('La capacidad debe ser finita y positiva.')
    if not isinstance(archivos, (list, tuple)):
        raise ValueError('archivos debe ser una lista.')
    for x in archivos:
        if isinstance(x, bool) or not isinstance(x, Real) or not isfinite(x) or not 0 < x <= capacidad:
            raise ValueError('Cada tamaño debe ser finito, positivo y no superar la capacidad.')

def verificar_solucion(archivos, capacidad, discos):
    validar_entrada(archivos, capacidad)
    if not isinstance(discos, list) or any(not isinstance(d, list) or not d for d in discos):
        raise ValueError('La solución debe contener discos no vacíos.')
    if Counter(x for d in discos for x in d) != Counter(archivos):
        raise ValueError('La solución pierde, duplica o modifica archivos.')
    if any(fsum(d) > capacidad for d in discos):
        raise ValueError('La solución excede la capacidad.')
    return True
