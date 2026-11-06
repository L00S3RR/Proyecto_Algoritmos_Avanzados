# Bitácora del Avance 7

Fecha de actualización: 6 de noviembre de 2026. Las entradas registran el trabajo comprobado en esta actualización; no atribuyen retroalimentación docente ni actividades históricas no documentadas.

| Actividad | Hallazgo o corrección | Evidencia |
|---|---|---|
| Revisión inicial | Demostración fija, validación parcial solo de FFD, sin métricas persistidas | Código inicial revisado |
| Validación | Rechazo de capacidad inválida, archivos imposibles y datos no finitos; verificación de las tres alternativas | src/validation.py y pruebas |
| Algoritmo exacto | Corrección de descripción de programación dinámica a búsqueda con poda; incumbente FFD, simetría y límite temporal | src/algorithms/exact.py |
| Heurísticas | Cargas acumuladas para evitar sumar discos en cada exploración | src/algorithms/approximate.py |
| Generación | Eliminada alteración de random global; rangos coherentes y tres familias | src/generator.py |
| Integración | Carga JSON, generación, CLI, medición, exportación y gráficos | src/main.py y src/experiments.py |
| Dependencias | Retirado python>=3.8 de requirements; Python se instala por separado | requirements.txt y README.md |
| Control de versiones | La exclusión global ocultaba pruebas y documentación nuevas; reemplazada por exclusiones de cachés | .gitignore |
| Pruebas | 55 pruebas aprobadas; comparación exacta con oráculo en 70 instancias | results/avance7/pruebas.xml |
| Experimentos | 66 instancias, 3 repeticiones y 3 algoritmos, 594 registros; 513 correctos y 81 omisiones | results/avance7/metricas.csv |
| Documentación | Manual, lista de evidencias e informe Word actualizados | README.md y docs/ |

## Dificultades pendientes

Ampliar familias adversarias y semillas; estudiar casos exactos que agoten el límite; separar efecto de ordenamiento y colocación; incorporar calentamiento y un protocolo estadístico más amplio. Los decimales arbitrarios conservan la aritmética binaria de Python: preferir unidades enteras. Las pruebas verifican comportamiento y casos pequeños, no constituyen una prueba matemática general.

## Correcciones de avances anteriores

Las correcciones se basan en problemas observados en el repositorio. No se encontró una bitácora previa ni observaciones docentes con las cuales certificar el cierre de comentarios específicos. Antes de la segunda entrega, el grupo debe contrastar esta lista con la retroalimentación recibida y añadir responsables y acuerdos reales.
