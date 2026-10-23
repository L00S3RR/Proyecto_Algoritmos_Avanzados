# Proyecto: Bin Packing 1D aplicado a backups

Este proyecto asigna archivos a discos de capacidad fija minimizando la cantidad de discos.
Para los avances 4 y 5, la demostracion compara **First Fit Decreasing (FFD)** con **Branch and Bound exacto**. Best Fit Decreasing (BFD) queda disponible como alternativa adicional. Las tres alternativas comparten formato, validacion y presentacion.

## Requisitos e instalacion

- Python 3.8 o superior.
- unittest (biblioteca estandar); tambien compatible con pytest.

```powershell
python -m pip install -r requirements.txt
```

El flujo principal usa solo la biblioteca estandar de Python. Pandas y Matplotlib ya no son necesarios para ejecutar el prototipo.

## Ejecucion

Desde la raiz de `entrega1`:

```powershell
# Ejecuta FFD, BFD y exacto sobre una instancia de demostracion
python src\main.py

# Ejecuta una alternativa especifica
python src\main.py --algorithm ffd
python src\main.py --algorithm exact

# Carga una instancia JSON
python src\main.py --instance data\instances\instancia_pequena.json --algorithm compare

# Escribe una instancia manual en la sesion
python src\main.py --files 4,3,2.5,2,1.5,1 --capacity 5 --algorithm compare

# Genera una instancia reproducible; el exacto se omite si excede 28 archivos
python src\main.py --generate 20 --capacity 100 --seed 42 --algorithm compare

# Ejecuta las pruebas automatizadas
python -m unittest discover -s tests -v
# Alternativa, si pytest esta instalado:
python -m pytest -q
```

Formato JSON: `{"capacity": 10, "files": [6, 6, 4, 4]}`. `--algorithm compare` corre las tres alternativas en la misma instancia. Para comparar solo FFD con el exacto, usar `--algorithm ffd` y `--algorithm exact` sobre el mismo archivo.

## Algoritmos y limites

- **FFD:** orden descendente; cada archivo va al primer disco con espacio suficiente. Aproximado, O(n log n + nB) con B discos en esta implementacion.
- **BFD:** orden descendente; elige el disco que queda con menos espacio libre. Aproximado, O(n log n + nB).
- **Branch and Bound:** busca la cantidad minima y poda asignaciones que no pueden mejorar la mejor solucion conocida. Exacto en instancias pequenas; su peor caso es exponencial y el limite predeterminado es 28 archivos.

Todas las alternativas validan capacidad y tamanos positivos finitos. Se conserva el valor de cada archivo en la salida y se comprueba que no falte ni se duplique ningun elemento.

## Estructura

```text
src/algorithms/approximate.py   FFD y BFD
src/algorithms/exact.py         Branch and Bound
src/validation.py               validacion comun de entradas y salidas
src/generator.py                generador reproducible
src/main.py                     CLI e integracion comun
tests/test_algorithms.py       pruebas basicas, limite, adversas e integracion
 data/instances/                instancias de demostracion
 docs/AVANCES_4_5.md            guion y correspondencia de los avances
```

## Estado

El prototipo de los avances 4 y 5 incluye ejecucion funcional, generacion y carga JSON, interfaz comun, validacion automatica, comparacion contra la alternativa exacta en instancias pequenas y pruebas automatizadas. La ejecucion en AWS y el informe final semestral permanecen fuera de estos dos avances.


