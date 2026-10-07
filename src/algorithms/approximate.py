"""Algoritmos aproximados para bin packing 1D."""

def first_fit_decreasing(archivos: list, capacidad: int) -> list:
    """Implementa el algoritmo First Fit Decreasing (FFD).
    
    Args:
        archivos: Lista de tamaños de archivos.
        capacidad: Capacidad de cada disco.
    
    Returns:
        Lista de discos, donde cada disco es una lista de archivos.
    """
    archivos_ordenados = sorted(archivos, reverse=True)
    discos = []
    
    for archivo in archivos_ordenados:
        colocado = False
        for disco in discos:
            if sum(disco) + archivo <= capacidad:
                disco.append(archivo)
                colocado = True
                break
        if not colocado:
            discos.append([archivo])
    
    return discos

def best_fit_decreasing(archivos: list, capacidad: int) -> list:
    """Implementa el algoritmo Best Fit Decreasing (BFD).
    
    Args:
        archivos: Lista de tamaños de archivos.
        capacidad: Capacidad de cada disco.
    
    Returns:
        Lista de discos, donde cada disco es una lista de archivos.
    """
    archivos_ordenados = sorted(archivos, reverse=True)
    discos = []
    
    for archivo in archivos_ordenados:
        mejor_disco = None
        menor_espacio = capacidad + 1
        
        for disco in discos:
            espacio_restante = capacidad - sum(disco)
            if espacio_restante >= archivo and espacio_restante < menor_espacio:
                mejor_disco = disco
                menor_espacio = espacio_restante
        
        if mejor_disco is not None:
            mejor_disco.append(archivo)
        else:
            discos.append([archivo])
    
    return discos
