# Bitácora - Avance 7

**Proyecto:** Bin Packing 1D para backups — Grupo 3, UNSAAC, 2026-2  
**Fecha de actualización:** 6 de noviembre de 2026

| Momento | Actividad o decisión | Evidencia / resultado |
|---|---|---|
| Revisión inicial | Se contrastó el estado del proyecto, informe de Entrega 1, avances 4-5, código, pruebas, JSON y carpeta de resultados. | Se confirmó FFD, BFD, Branch and Bound, carga JSON, generación y validación. No había resultados experimentales guardados. |
| Verificación funcional | Se ejecutó la suite automatizada completa. | 10 pruebas aprobadas. |
| Integración por archivo | Se corrió `compare` sobre `instancia_pequena.json` e `instancia_adversa.json`. | Las tres alternativas validaron las salidas: 2 discos y 3 discos, respectivamente. |
| Diseño de la medición | Se eligieron capacidad 100, seis tamaños entre 6 y 16, semillas 42–44 y cinco repeticiones por algoritmo/instancia. | 18 instancias; 54 filas y 270 mediciones temporales. El script vuelve a crear el CSV y el SVG. |
| Límite de escalabilidad observado | Un barrido inicial que incluía tamaños hasta 28 no terminó dentro de la ventana de ejecución. Se acotó el barrido publicado a `n <= 16`. | No se guardaron ni reportaron como resultados los casos incompletos. Se documentó que 28 es límite de entrada, no garantía de tiempo. |
| Análisis | Se compararon calidad y tiempo contra el exacto, y se contrastaron tendencias con la complejidad de las implementaciones. | Las heurísticas igualaron al óptimo en 17/18 sintéticas; ambas quedaron a +1 disco en una instancia de seis elementos. El exacto creció más rápido en esta muestra. |
| Preparación de entrega | Se actualizó documentación técnica y se organizaron evidencia tabular, gráfica e informe. | `README.md`, `docs/AVANCE_7.md`, `results/experiments/resultados_avance7.csv`, `results/experiments/tiempos_avance7.svg` y `src/experiments.py`. |

## Correcciones y decisiones consolidadas

- El algoritmo denominado exacto es Branch and Bound; la documentación previa ya había corregido la descripción errónea de programación dinámica.
- La medición usa la interfaz común y el verificador compartido; no se consideró válida una salida sin comprobar asignación completa y capacidad.
- Se separó la calidad de solución del tiempo. Con estos tamaños, las diferencias de pocos microsegundos son sensibles al entorno y no sostienen afirmaciones de rendimiento general.
- La corrida exploratoria que no terminó se excluyó de la tabla; los resultados publicados incluyen solo ejecuciones completas y verificadas.

## Dificultades y tareas pendientes

1. Branch and Bound no escala de forma práctica a todos los tamaños permitidos; se recomienda incorporar timeout explícito en futuros experimentos.
2. El conjunto sintético es inicial y pequeño. Faltan más semillas, distribuciones adversas y casos que produzcan brechas variadas.
3. El equipo debe registrar versiones del intérprete y repetir en condiciones controladas para comparar tiempos.
4. La prueba física/AWS y la validación de asignación frente al almacenamiento real continúan pendientes en el estado general del proyecto.
5. Antes de enviar, incorporar los archivos al historial del repositorio y revisar el diff completo, especialmente porque los resultados y documentación forman parte de la evidencia de segunda entrega.

## Actualización del 18 de noviembre de 2026

- Se agregó un límite temporal configurable al algoritmo exacto y su manejo en la interfaz común.
- Se ampliaron los experimentos a tres distribuciones, 36 instancias y 108 filas de resultados; se guardaron instancias, versiones del entorno y estados de ejecución en `resultados_ampliados.csv`.
- Las 108 corridas terminaron sin timeout. FFD y BFD igualaron el número de discos del exacto en esta muestra.
- Se agregó una prueba de timeout y de parámetro inválido. La suite ahora contiene 11 pruebas.
- Sigue pendiente la validación física/AWS, que requiere acceso a infraestructura del equipo.

## Preparación de transferencia a EC2 (18 de noviembre de 2026)

- Se creó `src/upload_to_ec2.py` para asignar archivos locales por tamaño y transferirlos por SFTP a las carpetas montadas en EC2.
- Se añadió un modo de planificación sin conexión, comprobación de espacio libre, rechazo de sobrescrituras y verificación SHA-256 tras la carga.
- Se probó localmente la asignación con archivos de tamaños repetidos; la suite pasó con 12 pruebas. La transferencia real queda pendiente de ejecución desde la laptop con la IP y la clave privada del equipo.

## Evidencia ejecutada

- `python -m unittest discover -s tests -v` — 10 pruebas aprobadas.
- `python src\main.py --instance data\instances\instancia_pequena.json --algorithm compare` — todas las salidas válidas, 2 discos.
- `python src\main.py --instance data\instances\instancia_adversa.json --algorithm compare` — todas las salidas válidas, 3 discos.
- `python src\experiments.py` — 18 instancias, 3 alternativas, cinco mediciones por combinación; CSV y SVG regenerados.
