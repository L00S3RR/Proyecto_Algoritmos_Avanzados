"""Flujo reproducible de experimentos preliminares del Avance 7."""
import csv
import json
import math
import platform
import statistics
import sys
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter_ns
from src.algorithms.approximate import first_fit_decreasing, best_fit_decreasing
from src.algorithms.exact import bin_packing_exacto
from src.generator import generar_instancia
from src.validation import validar_entrada, verificar_solucion

ALGORITMOS = {'FFD': first_fit_decreasing, 'BFD': best_fit_decreasing, 'Exacto': bin_packing_exacto}

def cargar_instancia(ruta):
    data = json.loads(Path(ruta).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or 'archivos' not in data or 'capacidad' not in data:
        raise ValueError('JSON requiere archivos y capacidad.')
    validar_entrada(data['archivos'], data['capacidad'])
    return data

def ejecutar_instancia(data, repeticion=0, exact_max=20, timeout=1.0):
    archivos, capacidad = data['archivos'], data['capacidad']
    validar_entrada(archivos, capacidad)
    filas, soluciones = [], {}
    for nombre, algoritmo in ALGORITMOS.items():
        fila = dict(instancia=data.get('id', 'manual'), familia=data.get('familia', 'manual'),
                    semilla=data.get('semilla', ''), n=len(archivos), capacidad=capacidad,
                    repeticion=repeticion, algoritmo=nombre, estado='ok', tiempo_ms=None,
                    memoria_kib=None, discos=None, cota_inferior=math.ceil(math.fsum(archivos)/capacidad),
                    desperdicio=None, utilizacion=None, brecha_opt_pct=None, verificado=False)
        if nombre == 'Exacto' and len(archivos) > exact_max:
            fila['estado'] = 'omitido_por_tamano'
            filas.append(fila)
            continue
        kwargs = {'limite_segundos': timeout} if nombre == 'Exacto' else {}
        inicio = perf_counter_ns()
        try:
            solucion = algoritmo(archivos, capacidad, **kwargs)
            fila['tiempo_ms'] = (perf_counter_ns() - inicio) / 1e6
            verificar_solucion(archivos, capacidad, solucion)
            # La memoria se mide en una ejecución separada, sin contaminar tiempo_ms.
            tracemalloc.start()
            try:
                algoritmo(archivos, capacidad, **kwargs)
                fila['memoria_kib'] = tracemalloc.get_traced_memory()[1] / 1024
            except TimeoutError:
                pass  # La corrida principal sí certificó el óptimo.
            finally:
                tracemalloc.stop()
            k = len(solucion)
            fila.update(discos=k, desperdicio=k*capacidad-math.fsum(archivos),
                        utilizacion=math.fsum(archivos)/(k*capacidad) if k else 1.0,
                        verificado=True)
            soluciones[nombre] = solucion
        except TimeoutError:
            fila.update(estado='limite_de_tiempo', tiempo_ms=(perf_counter_ns()-inicio)/1e6)
        filas.append(fila)
    if 'Exacto' in soluciones:
        opt = len(soluciones['Exacto'])
        for fila in filas:
            if fila['estado'] == 'ok':
                fila['brecha_opt_pct'] = 100*(fila['discos']-opt)/opt if opt else 0.0
    return filas, soluciones

def guardar_csv(ruta, filas):
    if not filas:
        return
    with Path(ruta).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)

def resumir(filas):
    grupos = {}
    for fila in filas:
        grupos.setdefault((fila['familia'], fila['n'], fila['algoritmo']), []).append(fila)
    resumen = []
    for (familia, n, algoritmo), grupo in grupos.items():
        ok = [f for f in grupo if f['estado'] == 'ok']
        def media(campo):
            valores = [f[campo] for f in ok if f[campo] is not None]
            return statistics.mean(valores) if valores else None
        tiempos = [f['tiempo_ms'] for f in ok]
        resumen.append(dict(familia=familia, n=n, algoritmo=algoritmo, ejecuciones=len(grupo),
                            correctas=len(ok), limites=sum(f['estado']=='limite_de_tiempo' for f in grupo),
                            omitidas=sum(f['estado']=='omitido_por_tamano' for f in grupo),
                            tiempo_mediana_ms=statistics.median(tiempos) if tiempos else None,
                            tiempo_min_ms=min(tiempos) if tiempos else None,
                            tiempo_max_ms=max(tiempos) if tiempos else None,
                            memoria_media_kib=media('memoria_kib'), discos_media=media('discos'),
                            utilizacion_media=media('utilizacion'), brecha_media_pct=media('brecha_opt_pct')))
    return resumen

def graficar(resumen, carpeta):
    import os
    import tempfile
    os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir())/"binpacking-matplotlib"))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    for ax, familia in zip(axes, ['uniforme', 'pequenos', 'grandes']):
        for algoritmo in ALGORITMOS:
            datos = sorted([r for r in resumen if r['familia']==familia and r['algoritmo']==algoritmo
                            and r['tiempo_mediana_ms'] is not None], key=lambda r:r['n'])
            ax.plot([r['n'] for r in datos], [r['tiempo_mediana_ms'] for r in datos], 'o-', label=algoritmo)
        ax.set(xscale='log', yscale='log', xlabel='Número de archivos', ylabel='Mediana ms', title=familia)
        ax.grid(alpha=.25)
    axes[0].legend()
    fig.tight_layout()
    fig.savefig(carpeta/'tiempos.png', dpi=170)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 3.5))
    casos = [r for r in resumen if r['familia']=='contraejemplo']
    ax.bar([r['algoritmo'] for r in casos], [r['discos_media'] for r in casos], color=['#50789b','#78a39b','#555555'])
    ax.set(ylabel='Discos', title='Instancia 6 5 3 2 2 2 con capacidad 10', ylim=(0,4))
    fig.tight_layout()
    fig.savefig(carpeta/'calidad.png', dpi=170)
    plt.close(fig)

def ejecutar_experimentos(carpeta='results/avance7', tamanos=(8,12,16,20,100,300,1000),
                         semillas=(11,42,99), repeticiones=3, exact_max=20, timeout=1.0):
    if repeticiones < 1 or exact_max < 0 or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('Repeticiones, límite exacto o tiempo inválidos.')
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    instancias = []
    for familia in ('uniforme','pequenos','grandes'):
        for n in tamanos:
            for semilla in semillas:
                instancias.append(dict(id=f'{familia}_{n}_{semilla}', familia=familia, semilla=semilla,
                                       capacidad=100, archivos=generar_instancia(n,100,semilla,familia)))
    instancias.extend([dict(id='contraejemplo', familia='contraejemplo', capacidad=10, archivos=[6,5,3,2,2,2]),
                       dict(id='vacia', familia='vacia', capacidad=10, archivos=[]),
                       dict(id='decimales', familia='decimales', capacidad=5, archivos=[4,3,2.5,2,1.5,1])])
    todas, evidencia = [], []
    for data in instancias:
        for rep in range(repeticiones):
            filas, soluciones = ejecutar_instancia(data, rep, exact_max, timeout)
            todas.extend(filas)
            if rep == 0:
                evidencia.append(dict(instancia=data['id'], soluciones=soluciones))
    resumen = resumir(todas)
    guardar_csv(carpeta/'metricas.csv', todas)
    guardar_csv(carpeta/'resumen.csv', resumen)
    for nombre, contenido in [('instancias.json',instancias), ('soluciones.json',evidencia),
        ('entorno.json',dict(fecha_utc=datetime.now(timezone.utc).isoformat(), python=sys.version,
            plataforma=platform.platform(), procesador=platform.processor(), tamanos=list(tamanos),
            semillas=list(semillas), repeticiones=repeticiones, exact_max=exact_max, timeout=timeout,
            medicion='Tiempo con perf_counter_ns; memoria pico Python con tracemalloc en corrida separada'))]:
        (carpeta/nombre).write_text(json.dumps(contenido,ensure_ascii=False,indent=2),encoding='utf-8')
    graficar(resumen, carpeta)
    return todas
