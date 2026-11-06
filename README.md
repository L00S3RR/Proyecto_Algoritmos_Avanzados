# Bin Packing 1D para asignación de archivos a discos

Sistema integrado del Avance 7. Compara First Fit Decreasing (FFD), Best Fit Decreasing (BFD) y búsqueda exacta con poda. La capacidad y los tamaños deben usar la misma unidad.

## Instalación

Requiere Python 3.10 o superior.

~~~powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
~~~

La dependencia Python no se instala mediante requirements.txt. Para generar nuevamente el Word, instalar también requirements-report.txt.

## Ejecución

Ejecutar desde la raíz del repositorio:

~~~powershell
python -m src.main
python -m src.main --entrada examples/instancia.json --salida results/manual
python -m src.main --n 100 --capacidad 100 --semilla 42 --familia uniforme --salida results/generada
python -m src.main --experimentos --repeticiones 3 --exact-max 20 --timeout 0.2
python -m pytest -q --junitxml=results/avance7/pruebas.xml
~~~

También se admite python src/main.py. El modo sin parámetros ejecuta el ejemplo original y guarda results/avance7/ejecucion.json. El modo experimental guarda sus resultados en results/avance7 salvo que se use --salida. No ejecutar simultáneamente dos procesos sobre la misma carpeta de salida.

## Parámetros

| Parámetro | Descripción | Valor predeterminado |
|---|---|---|
| --entrada | Ruta JSON de una instancia | Sin archivo |
| --n | Cantidad de archivos generados | Demostración si no hay entrada |
| --capacidad | Capacidad entera de la generación | 100 |
| --semilla | Semilla local del generador | 42 |
| --familia | uniforme, pequenos o grandes | uniforme |
| --experimentos | Ejecuta el protocolo fijo | Desactivado |
| --salida | Directorio de resultados | results/avance7 |
| --repeticiones | Repeticiones por instancia del protocolo | 3 |
| --exact-max | Máximo n para ejecutar el exacto | 20 |
| --timeout | Segundos por corrida exacta | 1.0 |

El protocolo utiliza tamaños 8, 12, 16, 20, 100, 300 y 1000; semillas 11, 42 y 99; capacidad 100 y tres familias. Añade casos vacío, decimal y un contraejemplo de las heurísticas. --n, --entrada y parámetros del generador corresponden a ejecución individual; la matriz experimental se define en src/experiments.py.

## Formatos y validación

Entrada JSON: {"id":"caso1","capacidad":10,"archivos":[6,5,3,2,2,2]}. id es opcional. Capacidad finita positiva; tamaños finitos positivos menores o iguales a ella. Se admite lista vacía. Se rechazan booleanos y cadenas numéricas. Para medidas físicas se recomienda convertir a unidades enteras (por ejemplo MB) y evitar errores de punto flotante. La generación usa exclusivamente capacidad entera y n entero no negativo.

Salida individual: entrada, metricas y soluciones; cada solución es una lista de discos y cada disco una lista de tamaños. El verificador conserva multiplicidades y comprueba capacidad y discos no vacíos. Los errores de entrada terminan con código 2 y mensaje de argparse.

## Organización de resultados

- metricas.csv: una fila por instancia, algoritmo y repetición. Incluye estado, tiempo_ms, memoria_kib, discos, cota_inferior, desperdicio, utilizacion, brecha_opt_pct y verificado.
- resumen.csv: agrupación por familia, tamaño y algoritmo, con mediana, mínimo y máximo de tiempo y medias de calidad y memoria; contabiliza estados.
- instancias.json: entradas exactas utilizadas; soluciones.json: soluciones de la primera repetición.
- entorno.json: plataforma, Python y configuración de reproducción.
- tiempos.png y calidad.png: gráficos iniciales.
- pruebas.xml: evidencia JUnit de pruebas, generada por pytest.

Estado ok significa solución verificada. limite_de_tiempo indica óptimo no certificado; omitido_por_tamano indica omisión deliberada. Las métricas no disponibles quedan vacías, nunca como cero. La brecha solo se calcula cuando hay óptimo certificado. Los tiempos usan perf_counter_ns; la memoria usa tracemalloc en una segunda ejecución y representa asignaciones Python, no RSS del proceso. Si esta segunda ejecución exacta agota el tiempo, la memoria queda vacía y se conserva el resultado de la primera.

## Módulos y complejidad

- src/main.py: CLI, selección de entrada, generación y exportación individual.
- src/validation.py: validación de entrada y verificación independiente de factibilidad.
- src/generator.py: generador con random.Random local; uniforme en [1,C], pequenos en [1,max(1,C//4)] y grandes en [C//2+1,C].
- src/algorithms/approximate.py: FFD y BFD con cargas acumuladas. Ordenación O(n log n), exploración O(n²), espacio O(n).
- src/algorithms/exact.py: búsqueda en profundidad con incumbente FFD y poda de cargas simétricas; peor caso combinatorio, cota conservadora O(n^n), espacio O(n²) en el peor caso por los conjuntos de simetría de los niveles recursivos; solución y cargas O(n). El límite temporal no transforma una solución parcial en un óptimo.
- src/experiments.py: protocolo, medición, resumen y gráficos.
- tests/: pruebas originales y ampliadas, incluido oráculo exhaustivo independiente para 70 instancias pequeñas.
- scripts/generar_informe.py: construye el informe Word a partir de evidencias guardadas.

## Reproducción de la evidencia entregada

Ejecutar los comandos de experimentos y pruebas anteriores. Mantener semillas, tamaños, versión de Python y dependencias de results/avance7/dependencias.txt para comparación. Las instancias y el número de discos se reproducen; los tiempos y la memoria varían con el equipo y la carga. Las repeticiones de una misma semilla no son instancias independientes. El experimento es preliminar, sin inferencia estadística ni garantía empírica general de optimalidad de FFD o BFD.

Para regenerar el informe: python -m pip install -r requirements-report.txt y python scripts/generar_informe.py. El documento entregado está en docs/Informe_Avance_7.docx. Consultar docs/BITACORA.md y docs/SEGUNDA_ENTREGA.md.
