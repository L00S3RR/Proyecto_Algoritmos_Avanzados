"""Interfaz de línea de comandos interactiva para Bin Packing 1D (FFD / BFD)."""
import json
import math
import sys
import tracemalloc
from pathlib import Path
from time import perf_counter_ns

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.algorithms.approximate import first_fit_decreasing, best_fit_decreasing
from src.algorithms.exact import bin_packing_exacto
from src.generator import generar_instancia
from src.validation import validar_entrada, verificar_solucion

# ──────────────────────────────────────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────────────────────────────────────

ALGORITMOS_MAP = {
    'FFD':    ('First Fit Decreasing',          first_fit_decreasing),
    'BFD':    ('Best Fit Decreasing',           best_fit_decreasing),
    'Exacto': ('Búsqueda Exacta con Poda',      bin_packing_exacto),
}
# Orden de alternado FFD <-> BFD (AMBOS y Exacto no participan del ciclo rápido)
_CICLO_TOGGLE = ['FFD', 'BFD']

BAR_WIDTH   = 30   # caracteres de la barra de llenado
PAGE_SIZE   = 20   # discos por página en el modo paginado

# ──────────────────────────────────────────────────────────────────────────────
# Utilidades de presentación
# ──────────────────────────────────────────────────────────────────────────────

def colorear(texto: str, estilo: str) -> str:
    """Aplica códigos ANSI si stdout es una terminal interactiva."""
    if not sys.stdout.isatty():
        return texto
    estilos = {
        'negrita':  '\033[1m',
        'cyan':     '\033[96m',
        'verde':    '\033[92m',
        'amarillo': '\033[93m',
        'rojo':     '\033[91m',
        'azul':     '\033[94m',
        'gris':     '\033[90m',
        'reset':    '\033[0m',
    }
    prefijo = estilos.get(estilo, '')
    return f"{prefijo}{texto}{estilos['reset']}" if prefijo else texto


def _barra(carga: float, capacidad: float, ancho: int = BAR_WIDTH) -> str:
    """Devuelve una barra ASCII proporcional al llenado del disco.

    Ejemplo (ancho=20, llenado 75%):  ███████████████░░░░░
    """
    pct    = min(carga / capacidad, 1.0) if capacidad > 0 else 0.0
    lleno  = round(pct * ancho)
    vacio  = ancho - lleno
    return '█' * lleno + '░' * vacio


def _color_pct(pct: float) -> str:
    """Color semáforo según el porcentaje de llenado."""
    if pct >= 95:
        return 'verde'
    if pct >= 70:
        return 'amarillo'
    return 'rojo'


# ──────────────────────────────────────────────────────────────────────────────
# Visualización de discos
# ──────────────────────────────────────────────────────────────────────────────

def _mostrar_discos(solucion: list, capacidad: float, mostrar_archivos: bool,
                    inicio: int = 0, fin: int | None = None) -> None:
    """Imprime cada disco con barra de llenado y, opcionalmente, la lista de archivos.

    Args:
        solucion: lista de discos (cada disco es lista de tamaños).
        capacidad: capacidad del disco.
        mostrar_archivos: si True, muestra los tamaños asignados a cada disco.
        inicio / fin: rango de discos a mostrar (soporte de paginación).
    """
    if fin is None:
        fin = len(solucion)

    for idx in range(inicio, min(fin, len(solucion))):
        disco  = solucion[idx]
        carga  = math.fsum(disco)
        pct    = (carga / capacidad * 100) if capacidad > 0 else 0.0
        barra  = _barra(carga, capacidad)
        color  = _color_pct(pct)
        num    = idx + 1

        # Línea principal: número, barra, carga/cap, porcentaje, cantidad de archivos
        linea_barra = (
            f"  Disco {num:>4d}  "
            + colorear(barra, color)
            + f"  [{carga:>7.2f} / {capacidad} | {colorear(f'{pct:5.1f}%', color)}]"
            + colorear(f"  ({len(disco)} arch.)", 'gris')
        )
        print(linea_barra)

        if mostrar_archivos:
            # Muestra los archivos en columnas de hasta 10 por línea
            por_linea = 10
            for i in range(0, len(disco), por_linea):
                trozo = disco[i: i + por_linea]
                print(colorear("             └─ ", 'gris') + "  ".join(str(x) for x in trozo))


def _paginar_discos(solucion: list, capacidad: float, mostrar_archivos: bool) -> None:
    """Muestra los discos paginados cuando hay más de PAGE_SIZE discos."""
    total  = len(solucion)
    pagina = 0
    total_pags = math.ceil(total / PAGE_SIZE)

    while True:
        ini = pagina * PAGE_SIZE
        fin = min(ini + PAGE_SIZE, total)
        print(colorear(
            f"\n  Discos {ini + 1}–{fin} de {total}  "
            f"(página {pagina + 1}/{total_pags}):", 'negrita'
        ))
        _mostrar_discos(solucion, capacidad, mostrar_archivos, inicio=ini, fin=fin)

        if total_pags == 1:
            break

        print()
        nav_opts = []
        if pagina > 0:
            nav_opts.append(colorear('[A] Anterior', 'amarillo'))
        if pagina < total_pags - 1:
            nav_opts.append(colorear('[S] Siguiente', 'amarillo'))
        nav_opts.append(colorear('[Q] Terminar paginación', 'rojo'))
        print("  " + "  |  ".join(nav_opts))

        try:
            tecla = input("  Opción: ").strip().upper()
        except (KeyboardInterrupt, EOFError):
            break

        if tecla == 'S' and pagina < total_pags - 1:
            pagina += 1
        elif tecla == 'A' and pagina > 0:
            pagina -= 1
        elif tecla in ('Q', ''):
            break


# ──────────────────────────────────────────────────────────────────────────────
# Ejecución de algoritmos
# ──────────────────────────────────────────────────────────────────────────────

def resolver_con_algoritmo(nombre_alg: str, archivos: list, capacidad: float) -> dict:
    """Ejecuta un algoritmo y retorna métricas + solución."""
    _, func = ALGORITMOS_MAP[nombre_alg]
    kwargs  = {'limite_segundos': 30.0} if nombre_alg == 'Exacto' else {}
    inicio  = perf_counter_ns()
    try:
        solucion   = func(archivos, capacidad, **kwargs)
        tiempo_ms  = (perf_counter_ns() - inicio) / 1e6
        verificar_solucion(archivos, capacidad, solucion)

        # Medición de memoria pico en corrida separada
        tracemalloc.start()
        try:
            func(archivos, capacidad, **kwargs)
            memoria_kib = tracemalloc.get_traced_memory()[1] / 1024
        except TimeoutError:
            memoria_kib = None
        finally:
            tracemalloc.stop()

        k            = len(solucion)
        suma         = math.fsum(archivos)
        desperdicio  = k * capacidad - suma
        utilizacion  = (suma / (k * capacidad)) * 100 if k > 0 else 100.0

        return {
            'estado':      'ok',
            'tiempo_ms':   tiempo_ms,
            'memoria_kib': memoria_kib,
            'discos':      k,
            'desperdicio': desperdicio,
            'utilizacion': utilizacion,
            'solucion':    solucion,
        }
    except TimeoutError:
        return {
            'estado':    'limite_de_tiempo',
            'tiempo_ms': (perf_counter_ns() - inicio) / 1e6,
            'discos':    None,
            'solucion':  [],
        }
    except Exception as exc:
        return {
            'estado':    'error',
            'error':     str(exc),
            'tiempo_ms': (perf_counter_ns() - inicio) / 1e6,
            'discos':    None,
            'solucion':  [],
        }


# ──────────────────────────────────────────────────────────────────────────────
# Presentación de resultados
# ──────────────────────────────────────────────────────────────────────────────

def mostrar_resultado(instancia: dict, alg_seleccionado: str) -> None:
    """Imprime resultado completo: métricas + visualización de discos."""
    archivos      = instancia['archivos']
    capacidad     = instancia['capacidad']
    n             = len(archivos)
    suma          = math.fsum(archivos)
    cota_inferior = math.ceil(suma / capacidad) if capacidad > 0 else 0

    # Mostrar archivos individuales siempre que n ≤ 30
    mostrar_lista = n <= 30

    print("\n" + "=" * 72)
    print(colorear(f"  RESULTADOS: {instancia.get('id', 'Instancia')}", 'negrita'))
    print("=" * 72)
    print(f"  • Capacidad por disco    : {capacidad}")
    print(f"  • Archivos a distribuir  : {n}")
    print(f"  • Suma total de tamaños  : {suma:.2f}")
    print(f"  • Cota inferior teórica  : {cota_inferior} disco(s)")
    if mostrar_lista:
        print(f"  • Archivos               : {archivos}")
    print("-" * 72)

    algoritmos_a_correr = ['FFD', 'BFD'] if alg_seleccionado == 'AMBOS' else [alg_seleccionado]
    resultados: dict = {}

    for nombre in algoritmos_a_correr:
        desc, _ = ALGORITMOS_MAP[nombre]
        print(f"\n{colorear(f'► {nombre} — {desc}', 'cyan')}")
        res = resolver_con_algoritmo(nombre, archivos, capacidad)
        resultados[nombre] = res

        if res['estado'] == 'limite_de_tiempo':
            print(colorear(f"  ⚠ Tiempo agotado tras {res['tiempo_ms']:.1f} ms.", 'amarillo'))
            continue
        if res['estado'] != 'ok':
            print(colorear(f"  ✗ Error: {res.get('error', '?')}", 'rojo'))
            continue

        # ── Resumen numérico ──────────────────────────────────────────────
        print(f"  Discos utilizados    : {colorear(str(res['discos']), 'verde')}"
              f"  (cota inferior: {cota_inferior})")
        print(f"  Utilización media    : {res['utilizacion']:.2f}%  "
              f"  Desperdicio total: {res['desperdicio']:.2f}")
        t_ms = res['tiempo_ms']
        m_kib = res['memoria_kib']
        mem_str = f"{m_kib:.2f} KiB" if m_kib is not None else "n/d"
        print(f"  Tiempo de ejecución  : {t_ms:.4f} ms   "
              f"  Memoria pico: {mem_str}")

        # ── Visualización de discos ───────────────────────────────────────
        print()
        discos = res['discos']
        if discos == 0:
            print(colorear("  (Sin archivos — ningún disco utilizado)", 'gris'))
        elif discos <= PAGE_SIZE:
            print(colorear(
                f"  Organización de {discos} disco(s)"
                + ("  [se muestran archivos por disco]" if mostrar_lista else "  [usa opción 3 para instancias pequeñas]"),
                'negrita'
            ))
            _mostrar_discos(res['solucion'], capacidad, mostrar_lista)
        else:
            # Muchos discos → preguntar si paginar
            print(colorear(
                f"  {discos} discos generados. "
                f"{'Se muestran archivos.' if mostrar_lista else 'Lista de archivos omitida (n > 30).'} "
                "Paginando...",
                'negrita'
            ))
            _paginar_discos(res['solucion'], capacidad, mostrar_lista)

    # ── Comparativa cuando se ejecutan ambos algoritmos ───────────────────
    if len(algoritmos_a_correr) > 1:
        ok_res = {k: v for k, v in resultados.items() if v['estado'] == 'ok'}
        if len(ok_res) == 2:
            print("\n" + "-" * 72)
            print(colorear("  COMPARATIVA DIRECTA (FFD vs BFD):", 'negrita'))
            d_ffd = resultados['FFD']['discos']
            d_bfd = resultados['BFD']['discos']
            t_ffd = resultados['FFD']['tiempo_ms']
            t_bfd = resultados['BFD']['tiempo_ms']

            # Espacio
            if d_ffd == d_bfd:
                print(colorear(f"  • Discos: empate — ambos usan {d_ffd} disco(s).", 'verde'))
            elif d_ffd < d_bfd:
                ganador = colorear(f"FFD ({d_ffd} discos)", 'verde')
                print(f"  • Espacio: {ganador} vs BFD ({d_bfd} discos) ← FFD más eficiente")
            else:
                ganador = colorear(f"BFD ({d_bfd} discos)", 'verde')
                print(f"  • Espacio: FFD ({d_ffd} discos) vs {ganador} ← BFD más eficiente")

            # Tiempo
            if abs(t_ffd - t_bfd) < 0.001:
                print("  • Tiempo: prácticamente idéntico.")
            elif t_ffd < t_bfd:
                print(f"  • Tiempo: {colorear('FFD más rápido', 'verde')} "
                      f"({t_ffd:.4f} ms vs {t_bfd:.4f} ms BFD)")
            else:
                print(f"  • Tiempo: {colorear('BFD más rápido', 'verde')} "
                      f"({t_bfd:.4f} ms vs {t_ffd:.4f} ms FFD)")

    print("=" * 72 + "\n")


# ──────────────────────────────────────────────────────────────────────────────
# Submenús de configuración
# ──────────────────────────────────────────────────────────────────────────────

def configurar_instancia(instancia_actual: dict) -> dict:
    """Submenú para elegir o ingresar una instancia de datos."""
    while True:
        print("\n" + "─" * 55)
        print(colorear("  CONFIGURACIÓN DE LA INSTANCIA", 'negrita'))
        print("─" * 55)
        print("  1. Demostración    — capacidad 5,  archivos [4, 3, 2.5, 2, 1.5, 1]")
        print("  2. Contraejemplo   — capacidad 10, archivos [6, 5, 3, 2, 2, 2]")
        print("  3. Desde archivo JSON")
        print("  4. Ingresar datos manualmente")
        print("  5. Generar instancia sintética aleatoria")
        print("  0. Regresar sin cambios")

        opcion = input(colorear("\n  Opción (0-5): ", 'cyan')).strip()

        if opcion == '0':
            return instancia_actual

        elif opcion == '1':
            inst = {'id': 'demostracion', 'capacidad': 5,
                    'archivos': [4, 3, 2.5, 2, 1.5, 1]}
            print(colorear("  ✔ Instancia 'demostracion' cargada.", 'verde'))
            return inst

        elif opcion == '2':
            inst = {'id': 'contraejemplo', 'capacidad': 10,
                    'archivos': [6, 5, 3, 2, 2, 2]}
            print(colorear("  ✔ Instancia 'contraejemplo' cargada.", 'verde'))
            return inst

        elif opcion == '3':
            ruta_str = input("  Ruta del JSON [examples/instancia.json]: ").strip() \
                       or "examples/instancia.json"
            ruta = Path(ruta_str)
            if not ruta.exists():
                print(colorear(f"  ✗ Archivo no encontrado: '{ruta}'", 'rojo'))
                continue
            try:
                data = json.loads(ruta.read_text(encoding='utf-8'))
                if not isinstance(data, dict) or 'archivos' not in data or 'capacidad' not in data:
                    raise ValueError("El JSON debe tener las claves 'archivos' y 'capacidad'.")
                validar_entrada(data['archivos'], data['capacidad'])
                data.setdefault('id', ruta.stem)
                print(colorear(f"  ✔ Instancia '{data['id']}' cargada "
                               f"({len(data['archivos'])} archivos).", 'verde'))
                return data
            except Exception as exc:
                print(colorear(f"  ✗ Error: {exc}", 'rojo'))

        elif opcion == '4':
            try:
                cap_str = input("  Capacidad del disco: ").strip()
                cap = float(cap_str)
                if cap.is_integer():
                    cap = int(cap)
                items_str = input("  Tamaños de archivos (espacio o coma): ").strip()
                tokens   = items_str.replace(',', ' ').split()
                archivos: list = []
                for t in tokens:
                    v = float(t)
                    archivos.append(int(v) if v.is_integer() else v)
                validar_entrada(archivos, cap)
                print(colorear(f"  ✔ Instancia manual cargada ({len(archivos)} archivos).", 'verde'))
                return {'id': 'manual', 'capacidad': cap, 'archivos': archivos}
            except Exception as exc:
                print(colorear(f"  ✗ Datos inválidos: {exc}", 'rojo'))

        elif opcion == '5':
            try:
                n   = int(input("  Cantidad de archivos (n): ").strip())
                cap = int(input("  Capacidad entera [100]: ").strip() or "100")
                sem = int(input("  Semilla [42]: ").strip() or "42")
                print("  Familias: 1=uniforme  2=pequeños  3=grandes")
                fop = input("  Familia [1]: ").strip() or "1"
                fam = {'1': 'uniforme', '2': 'pequenos', '3': 'grandes'}.get(fop, 'uniforme')
                archivos = generar_instancia(n, cap, sem, fam)
                print(colorear(f"  ✔ Instancia generada: {n} archivos, familia '{fam}'.", 'verde'))
                return {'id': f"generada_{fam}_{n}", 'capacidad': cap, 'archivos': archivos}
            except Exception as exc:
                print(colorear(f"  ✗ Error al generar: {exc}", 'rojo'))

        else:
            print(colorear("  Opción no reconocida.", 'rojo'))


def seleccionar_algoritmo_menu(alg_actual: str) -> str:
    """Submenú para seleccionar explícitamente el algoritmo activo."""
    print("\n" + "─" * 45)
    print(colorear("  SELECCIÓN DE ALGORITMO", 'negrita'))
    print("─" * 45)
    opciones = [
        ('1', 'FFD',    'First Fit Decreasing'),
        ('2', 'BFD',    'Best Fit Decreasing'),
        ('3', 'AMBOS',  'Comparativa FFD vs BFD'),
        ('4', 'Exacto', 'Búsqueda Exacta con Poda'),
    ]
    for num, clave, desc in opciones:
        marca = colorear(' ◄ ACTUAL', 'verde') if clave == alg_actual else ''
        print(f"  {num}. {clave:7s} — {desc}{marca}")
    print(f"  0. Mantener actual ({colorear(alg_actual, 'verde')})")

    op = input(colorear("\n  Opción (0-4): ", 'cyan')).strip()
    mapeo = {'1': 'FFD', '2': 'BFD', '3': 'AMBOS', '4': 'Exacto'}
    nuevo = mapeo.get(op, alg_actual)
    if nuevo != alg_actual:
        print(colorear(f"  ✔ Algoritmo cambiado a: {nuevo}", 'verde'))
    return nuevo


# ──────────────────────────────────────────────────────────────────────────────
# Alternado rápido FFD ↔ BFD
# ──────────────────────────────────────────────────────────────────────────────

def alternar_algoritmo(alg_actual: str) -> str:
    """Cicla entre FFD y BFD (si el actual es AMBOS o Exacto, va a FFD)."""
    if alg_actual in _CICLO_TOGGLE:
        nuevo = _CICLO_TOGGLE[1 - _CICLO_TOGGLE.index(alg_actual)]
    else:
        nuevo = 'FFD'
    desc, _ = ALGORITMOS_MAP[nuevo]
    print(colorear(f"\n  ↔ Algoritmo cambiado a: {nuevo} ({desc})", 'verde'))
    return nuevo


# ──────────────────────────────────────────────────────────────────────────────
# Bucle principal
# ──────────────────────────────────────────────────────────────────────────────

def iniciar_interfaz_cli(instancia_inicial: dict | None = None,
                         algoritmo_inicial: str = 'FFD') -> None:
    """Bucle principal de la interfaz interactiva."""
    algoritmo_activo = algoritmo_inicial
    instancia_activa = instancia_inicial or {
        'id': 'demostracion',
        'capacidad': 5,
        'archivos': [4, 3, 2.5, 2, 1.5, 1],
    }

    print("\n" + "=" * 72)
    print(colorear("         BIN PACKING 1D — INTERFAZ CLI INTERACTIVA", 'negrita'))
    print("=" * 72)

    while True:
        if algoritmo_activo == 'AMBOS':
            desc_alg = "Comparar FFD y BFD"
        else:
            desc_alg = ALGORITMOS_MAP[algoritmo_activo][0]

        n_arch = len(instancia_activa['archivos'])
        cap    = instancia_activa['capacidad']

        print("\n" + "═" * 72)
        print(f"  Algoritmo : {colorear(algoritmo_activo, 'verde')}  ({desc_alg})")
        print(f"  Instancia : {colorear(instancia_activa.get('id', 'manual'), 'cyan')}  "
              f"— capacidad {cap}, {n_arch} archivo(s)")
        print("═" * 72)
        print(f"  [{colorear('1', 'amarillo')}]  Intercambiar rápido  FFD ↔ BFD")
        print(f"  [{colorear('2', 'amarillo')}]  Seleccionar algoritmo  (FFD / BFD / Ambos / Exacto)")
        print(f"  [{colorear('3', 'amarillo')}]  Cambiar instancia de datos")
        print(f"  [{colorear('4', 'verde')}]  EJECUTAR  algoritmo actual")
        print(f"  [{colorear('5', 'cyan')}]  COMPARAR  FFD vs BFD (en esta instancia)")
        print(f"  [{colorear('0', 'rojo')}]  Salir")
        print("─" * 72)

        try:
            opcion = input(colorear("  Opción: ", 'negrita')).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n  Saliendo de la interfaz CLI.")
            break

        if opcion == '1':
            algoritmo_activo = alternar_algoritmo(algoritmo_activo)
        elif opcion == '2':
            algoritmo_activo = seleccionar_algoritmo_menu(algoritmo_activo)
        elif opcion == '3':
            instancia_activa = configurar_instancia(instancia_activa)
        elif opcion == '4':
            mostrar_resultado(instancia_activa, algoritmo_activo)
        elif opcion == '5':
            mostrar_resultado(instancia_activa, 'AMBOS')
        elif opcion == '0' or opcion.lower() in ('q', 'exit', 'salir'):
            print(colorear("\n  ¡Hasta luego!\n", 'cyan'))
            break
        else:
            print(colorear("  Opción no válida. Intente de nuevo.", 'rojo'))


if __name__ == '__main__':
    iniciar_interfaz_cli()
