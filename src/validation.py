"""Validacion compartida de instancias y soluciones de bin packing."""
from decimal import Decimal, InvalidOperation
import math


def _decimal_positivo(valor, nombre):
    if isinstance(valor, bool):
        raise ValueError(f"{nombre} debe ser un numero positivo, no booleano")
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{nombre} debe ser un numero valido") from None
    if not numero.is_finite() or numero <= 0:
        raise ValueError(f"{nombre} debe ser finito y mayor que cero")
    return numero


def normalize_instance(archivos, capacidad):
    """Devuelve (valor_original, Decimal) y capacidad Decimal tras validar."""
    if not isinstance(archivos, (list, tuple)):
        raise ValueError("La lista de archivos debe ser una lista o tupla")
    cap = _decimal_positivo(capacidad, "La capacidad")
    items = []
    for i, valor in enumerate(archivos):
        tamano = _decimal_positivo(valor, f"El archivo {i + 1}")
        if tamano > cap:
            raise ValueError(f"El archivo {i + 1} ({valor}) excede la capacidad ({capacidad})")
        items.append((valor, tamano))
    return items, cap


def validate_solution(archivos, capacidad, discos):
    """Valida que la salida conserve cada archivo y respete todas las capacidades."""
    items, cap = normalize_instance(archivos, capacidad)
    if not isinstance(discos, (list, tuple)):
        return False, "La solucion debe ser una lista de discos"
    try:
        esperados = sorted(t for _, t in items)
        obtenidos = []
        for i, disco in enumerate(discos):
            if not isinstance(disco, (list, tuple)) or not disco:
                return False, f"El disco {i + 1} esta vacio o tiene formato invalido"
            total = Decimal(0)
            for valor in disco:
                tamano = _decimal_positivo(valor, f"Elemento del disco {i + 1}")
                total += tamano
                obtenidos.append(tamano)
            if total > cap:
                return False, f"El disco {i + 1} excede la capacidad: {total} > {cap}"
        if sorted(obtenidos) != esperados:
            return False, "La solucion omitio, duplico o modifico archivos"
    except ValueError as exc:
        return False, str(exc)
    return True, "Todos los archivos estan asignados y las capacidades se respetan"
