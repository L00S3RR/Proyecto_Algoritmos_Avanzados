"""Algoritmo exacto para bin packing 1D usando programación dinámica."""

def bin_packing_exacto(archivos: list, capacidad: int) -> list:
    """Resuelve el bin packing 1D de forma exacta usando programación dinámica.
    
    Nota: Esta implementación es para instancias pequeñas.
    
    Args:
        archivos: Lista de tamaños de archivos.
        capacidad: Capacidad de cada disco.
    
    Returns:
        Lista de discos, donde cada disco es una lista de archivos.
    """
    n = len(archivos)
    if n == 0:
        return []
    
    # Para instancias pequeñas, usar búsqueda exhaustiva
    mejor_solucion = None
    
    def backtraking(idx, discos_actuales):
        nonlocal mejor_solucion
        if idx == n:
            if mejor_solucion is None or len(discos_actuales) < len(mejor_solucion):
                mejor_solucion = [d[:] for d in discos_actuales]
            return
        
        # Podar si ya tenemos demasiados discos
        if mejor_solucion is not None and len(discos_actuales) >= len(mejor_solucion):
            return
        
        # Probar colocar en disco existente
        for disco in discos_actuales:
            if sum(disco) + archivos[idx] <= capacidad:
                disco.append(archivos[idx])
                backtraking(idx + 1, discos_actuales)
                disco.pop()
        
        # Probar crear nuevo disco
        discos_actuales.append([archivos[idx]])
        backtraking(idx + 1, discos_actuales)
        discos_actuales.pop()
    
    backtraking(0, [])
    return mejor_solucion
