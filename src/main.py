"""Interfaz de línea de comandos del sistema integrado."""
import argparse
import json
import sys
from pathlib import Path
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.experiments import cargar_instancia, ejecutar_instancia, ejecutar_experimentos
from src.generator import generar_instancia

def main(argv=None):
    parser = argparse.ArgumentParser(description='Bin Packing 1D y experimentos del Avance 7')
    parser.add_argument('--experimentos', action='store_true')
    parser.add_argument('--entrada', type=Path, help='JSON con archivos y capacidad')
    parser.add_argument('--n', type=int, help='Cantidad de archivos a generar')
    parser.add_argument('--capacidad', type=int, default=100)
    parser.add_argument('--semilla', type=int, default=42)
    parser.add_argument('--familia', choices=['uniforme','pequenos','grandes'], default='uniforme')
    parser.add_argument('--salida', type=Path, default=Path('results/avance7'))
    parser.add_argument('--repeticiones', type=int, default=3)
    parser.add_argument('--exact-max', type=int, default=20)
    parser.add_argument('--timeout', type=float, default=1.0)
    parser.add_argument('-a', '--algoritmo', choices=['ffd', 'bfd', 'exacto', 'todos'], default='todos', type=str.lower,
                        help='Algoritmo a ejecutar: ffd, bfd, exacto o todos (predeterminado: todos)')
    parser.add_argument('-i', '--interactivo', action='store_true',
                        help='Iniciar la interfaz interactiva en consola para alternar entre FFD y BFD')
    args = parser.parse_args(argv)
    try:
        if args.exact_max < 0 or args.timeout <= 0 or not __import__('math').isfinite(args.timeout):
            raise ValueError('exact-max debe ser no negativo y timeout finito positivo.')
        if args.entrada is not None and args.n is not None:
            raise ValueError('Seleccione entrada o generación con n.')
        if args.interactivo:
            from src.cli import iniciar_interfaz_cli
            instancia_ini = None
            if args.entrada:
                instancia_ini = cargar_instancia(args.entrada)
            elif args.n is not None:
                instancia_ini = dict(id='generada', capacidad=args.capacidad,
                                     archivos=generar_instancia(args.n, args.capacidad, args.semilla, args.familia))
            alg_ini = 'FFD' if args.algoritmo == 'todos' else (args.algoritmo.upper() if args.algoritmo.lower() != 'exacto' else 'Exacto')
            iniciar_interfaz_cli(instancia_inicial=instancia_ini, algoritmo_inicial=alg_ini)
            return
        if args.experimentos:
            if args.entrada is not None or args.n is not None:
                raise ValueError('El protocolo experimental utiliza sus propias instancias.')
            filas = ejecutar_experimentos(args.salida, repeticiones=args.repeticiones,
                                          exact_max=args.exact_max, timeout=args.timeout)
            print(f'Experimentos completados: {len(filas)} registros en {args.salida}')
        else:
            if args.entrada:
                data = cargar_instancia(args.entrada)
            elif args.n is not None:
                data = dict(id='generada', capacidad=args.capacidad,
                            archivos=generar_instancia(args.n,args.capacidad,args.semilla,args.familia))
            else:
                data = dict(id='demostracion',capacidad=5,archivos=[4,3,2.5,2,1.5,1])
            algs_sel = None if args.algoritmo == 'todos' else [args.algoritmo.upper() if args.algoritmo.lower() != 'exacto' else 'Exacto']
            filas, soluciones = ejecutar_instancia(data, exact_max=args.exact_max, timeout=args.timeout, algoritmos=algs_sel)
            args.salida.mkdir(parents=True,exist_ok=True)
            salida = dict(entrada=data,metricas=filas,soluciones=soluciones)
            (args.salida/'ejecucion.json').write_text(json.dumps(salida,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps(salida,ensure_ascii=False,indent=2))
    except (ValueError,OSError,RecursionError) as error:
        parser.error(str(error))

if __name__ == '__main__':
    main()
