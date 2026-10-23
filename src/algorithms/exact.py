"""Branch and Bound para instancias pequenas de bin packing 1D."""
from src.validation import normalize_instance

MAX_ITEMS_EXACT = 28


def bin_packing_exacto(archivos: list, capacidad: float, max_items: int = MAX_ITEMS_EXACT) -> list:
    """Busca el minimo de discos. Es exacto, pero exponencial en el peor caso."""
    items, cap = normalize_instance(archivos, capacidad)
    if len(items) > max_items:
        raise ValueError(f"Branch and Bound admite hasta {max_items} archivos; recibido: {len(items)}")
    if not items:
        return []
    items.sort(key=lambda item: item[1], reverse=True)
    # FFD da una cota superior inicial para podar la busqueda.
    from src.algorithms.approximate import first_fit_decreasing
    mejor = first_fit_decreasing([original for original, _ in items], capacidad)
    mejor_cantidad = len(mejor)
    discos, restantes = [], []

    def buscar(indice):
        nonlocal mejor, mejor_cantidad
        if indice == len(items):
            if len(discos) < mejor_cantidad:
                mejor = [[valor for valor in disco] for disco in discos]
                mejor_cantidad = len(discos)
            return
        if len(discos) >= mejor_cantidad:
            return
        archivo, tamano = items[indice]
        espacios_visitados = set()
        for i, espacio in enumerate(restantes):
            if espacio >= tamano and espacio not in espacios_visitados:
                espacios_visitados.add(espacio)
                discos[i].append(archivo)
                restantes[i] -= tamano
                buscar(indice + 1)
                restantes[i] += tamano
                discos[i].pop()
        if len(discos) + 1 < mejor_cantidad:
            discos.append([archivo])
            restantes.append(cap - tamano)
            buscar(indice + 1)
            discos.pop()
            restantes.pop()

    buscar(0)
    return mejor
