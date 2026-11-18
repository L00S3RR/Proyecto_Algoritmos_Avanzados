# Proyecto: Bin Packing 1D aplicado a backups

Este proyecto asigna archivos de distintos tamaños a discos de capacidad fija minimizando la cantidad de discos. La demostración compara **First Fit Decreasing (FFD)**, **Best Fit Decreasing (BFD)** y **Branch and Bound exacto**. Las alternativas comparten carga/generación, validación y formato de salida.

## Requisitos e instalación

- Python 3.8 o superior.
- El flujo principal y las pruebas usan la biblioteca estándar de Python; `requirements.txt` conserva pytest como alternativa para ejecutar la suite.

```powershell
python -m pip install -r requirements.txt
```

## Ejecución

Desde la raíz de `entrega1`:

```powershell
python src\main.py
python src\main.py --algorithm ffd
python src\main.py --instance data\instances\instancia_pequena.json --algorithm compare
python src\main.py --files 4,3,2.5,2,1.5,1 --capacity 5 --algorithm compare
python src\main.py --generate 20 --capacity 100 --seed 42 --algorithm compare
python -m unittest discover -s tests -v
```

El CLI acepta `--algorithm ffd|bfd|exact|compare`; `--max-exact-items` ajusta el límite de entrada exacta (28 por defecto) y `--exact-timeout` limita su búsqueda a 5 segundos por defecto. Al agotarse, informa que se omitió el exacto. `--instance` recibe JSON con formato `{"capacity": 10, "files": [6, 6, 4, 4]}`. También admite una lista JSON si se especifica `--capacity`. `--files` requiere tamaños separados por coma y `--capacity`; `--generate` requiere cantidad no negativa y capacidad entera positiva. `--seed` controla la generación reproducible (42 por defecto).

## Módulos y responsabilidades

| Ruta | Función |
|---|---|
| `src/main.py` | CLI: carga, genera, valida, ejecuta, mide, presenta y compara resultados. |
| `src/validation.py` | Normaliza/valida instancias y comprueba que cada elemento aparezca una vez y que se respete la capacidad. |
| `src/algorithms/approximate.py` | FFD y BFD. |
| `src/algorithms/exact.py` | Branch and Bound con cota inicial FFD y límite de elementos. |
| `src/generator.py` | Instancias enteras reproducibles con semilla. |
| `src/experiments.py` | Barrido preliminar, repetición de tiempos, verificación y exportación CSV/SVG. |
| `src/experiments_extended.py` | Barrido ampliado con tres distribuciones y registro del entorno. |
| `tests/test_algorithms.py` | Once pruebas unitarias/de integración con `unittest`; pytest puede descubrirlas. |
| `data/instances/` | Instancias JSON pequeñas y adversas de demostración. |
| `results/experiments/` | Resultados preliminares del Avance 7. |
| `docs/` | Guía de avances e informe/bitácora del Avance 7. |

## Salida y métricas

Para cada alternativa, la consola presenta asignación por disco, número de discos, tiempo, desperdicio total, utilización y estado de validación. En modo `compare`, Branch and Bound se usa como referencia exacta si el tamaño no supera el límite configurado. Sobre cada instancia `src/experiments.py` guarda una fila por algoritmo con `n`, semilla, capacidad, discos, desperdicio, utilización, mediana de cinco tiempos, validez y brecha en discos frente al exacto.

## Complejidad y límites

FFD y BFD ordenan y buscan entre discos: `O(n log n + nB)` con `B` discos abiertos, hasta `O(n²)` en esta implementación. Branch and Bound tiene peor caso exponencial y puede tardar demasiado antes de alcanzar su límite de 28 elementos; ese límite controla el tamaño de entrada, no el tiempo. Los tiempos de corridas pequeñas son sensibles al equipo y deben interpretarse como preliminares.

## Reproducir Avance 7

```powershell
python -m unittest discover -s tests -v
python src\main.py --instance data\instances\instancia_pequena.json --algorithm compare
python src\main.py --instance data\instances\instancia_adversa.json --algorithm compare
python src\experiments.py
python -B src\experiments_extended.py
```

El experimento usa capacidad 100, `n = 6, 8, 10, 12, 14, 16`, semillas 42–44 y cinco mediciones por algoritmo e instancia. Regenera `results/experiments/resultados_avance7.csv` y `results/experiments/tiempos_avance7.svg`. La tabla, interpretación, registro de pruebas y pendientes están en `docs/AVANCE_7.md`; la bitácora se encuentra en `docs/BITACORA_AVANCE_7.md`.

## Evidencia existente y pendientes

El Avance 7 agrega resultados preliminares reproducibles, análisis frente a complejidad, instrucciones y bitácora. El barrido inicial incluye 18 instancias pequeñas. El barrido ampliado genera 36 instancias con tres distribuciones, tamaños 6, 10, 14 y 18, semillas 42–44, tres repeticiones y un límite de 0.5 segundos por corrida exacta; guarda el entorno, las instancias, los resultados y los tiempos en `results/experiments/resultados_ampliados.csv`. La validación física/AWS y la preparación del informe final siguen pendientes. Ver `docs/AVANCE_7.md` y `docs/BITACORA_AVANCE_7.md`.
