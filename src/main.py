"""CLI comun para cargar/generar instancias y comparar alternativas."""
import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from time import perf_counter

from src.algorithms.approximate import best_fit_decreasing, first_fit_decreasing
from src.algorithms.exact import MAX_ITEMS_EXACT, bin_packing_exacto
from src.generator import generar_instancia
from src.validation import normalize_instance, validate_solution

ALGORITHMS = {
    "ffd": first_fit_decreasing,
    "bfd": best_fit_decreasing,
    "exact": bin_packing_exacto,
}


def leer_instancia(args):
    if args.instance:
        datos = json.loads(Path(args.instance).read_text(encoding="utf-8"))
        if isinstance(datos, dict):
            archivos, capacidad = datos.get("files"), datos.get("capacity")
        elif isinstance(datos, list) and args.capacity is not None:
            archivos, capacidad = datos, args.capacity
        else:
            raise ValueError("JSON esperado: {\"capacity\": C, \"files\": [...]}")
    elif args.files is not None:
        if args.capacity is None:
            raise ValueError("--files requiere --capacity")
        try:
            archivos = [float(x.strip()) if "." in x else int(x.strip()) for x in args.files.split(",")]
        except ValueError:
            raise ValueError("--files debe contener numeros separados por comas") from None
        capacidad = args.capacity
    elif args.generate is not None:
        if args.capacity is None:
            raise ValueError("--generate requiere --capacity")
        if not args.capacity.is_integer():
            raise ValueError("La generacion requiere una capacidad entera")
        archivos = generar_instancia(args.generate, int(args.capacity), args.seed)
        capacidad = args.capacity
    else:
        archivos, capacidad = [4, 3, 2.5, 2, 1.5, 1], 5
    normalize_instance(archivos, capacidad)
    return archivos, capacidad


def ejecutar(nombre, archivos, capacidad, exact_timeout=None):
    funcion = ALGORITHMS[nombre]
    inicio = perf_counter()
    discos = funcion(archivos, capacidad, timeout_s=exact_timeout) if nombre == "exact" else funcion(archivos, capacidad)
    tiempo = perf_counter() - inicio
    valido, mensaje = validate_solution(archivos, capacidad, discos)
    if not valido:
        raise RuntimeError(f"Salida invalida de {nombre}: {mensaje}")
    usado = sum(sum(d) for d in discos)
    total_capacidad = len(discos) * capacidad
    desperdicio = total_capacidad - usado
    utilizacion = 100 * usado / total_capacidad if total_capacidad else 100.0
    return discos, tiempo, desperdicio, utilizacion


def mostrar(nombre, resultado, capacidad):
    discos, tiempo, desperdicio, utilizacion = resultado
    print(f"\n{nombre.upper()} | discos: {len(discos)} | tiempo: {tiempo:.6f} s")
    for i, disco in enumerate(discos, 1):
        print(f"  Disco {i}: {disco} = {sum(disco)}/{capacidad}")
    print(f"  Desperdicio total: {desperdicio}; utilizacion: {utilizacion:.2f}%")
    print("  Validacion: OK")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Bin Packing 1D: FFD, BFD y Branch and Bound")
    entrada = parser.add_mutually_exclusive_group()
    entrada.add_argument("--instance", help="JSON con capacity y files")
    entrada.add_argument("--files", help="tamanos separados por coma, ej. 4,3,2.5,2")
    entrada.add_argument("--generate", type=int, help="cantidad de archivos sinteticos")
    parser.add_argument("--capacity", type=float, help="capacidad comun de cada disco")
    parser.add_argument("--seed", type=int, default=42, help="semilla del generador (default: 42)")
    parser.add_argument("--algorithm", choices=["ffd", "bfd", "exact", "compare"], default="compare")
    parser.add_argument("--max-exact-items", type=int, default=MAX_ITEMS_EXACT)
    parser.add_argument("--exact-timeout", type=float, default=5.0, help="limite de segundos para el exacto (default: 5)")
    args = parser.parse_args(argv)
    try:
        archivos, capacidad = leer_instancia(args)
        if args.exact_timeout <= 0:
            raise ValueError("--exact-timeout debe ser positivo")
        print(f"Instancia: archivos={archivos}; capacidad={capacidad}")
        seleccion = ["ffd", "bfd", "exact"] if args.algorithm == "compare" else [args.algorithm]
        resultados = {}
        for nombre in seleccion:
            if nombre == "exact" and len(archivos) > args.max_exact_items:
                print(f"\nEXACT: omitido; {len(archivos)} archivos supera el limite configurado ({args.max_exact_items}).")
                continue
            try:
                resultados[nombre] = ejecutar(nombre, archivos, capacidad, args.exact_timeout)
            except TimeoutError as exc:
                print(f"\nEXACT: omitido; {exc}")
                continue
            mostrar(nombre, resultados[nombre], capacidad)
        if "exact" in resultados:
            optimo = len(resultados["exact"][0])
            print(f"\nReferencia exacta: minimo comprobado = {optimo} discos")
            for nombre in ("ffd", "bfd"):
                if nombre in resultados:
                    diferencia = len(resultados[nombre][0]) - optimo
                    print(f"{nombre.upper()} frente al optimo: {diferencia:+d} discos")
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
