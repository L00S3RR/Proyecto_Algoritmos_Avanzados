"""Genera el informe Word del Avance 7 desde las evidencias experimentales."""
import csv
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/avance7'
rows = list(csv.DictReader((OUT/'metricas.csv').open(encoding='utf-8')))
summary = list(csv.DictReader((OUT/'resumen.csv').open(encoding='utf-8')))
env = json.loads((OUT/'entorno.json').read_text(encoding='utf-8'))
instances = json.loads((OUT/'instancias.json').read_text(encoding='utf-8'))
xml = ET.parse(OUT/'pruebas.xml')
suites = list(xml.getroot().iter('testsuite'))
tests = sum(int(s.get('tests',0)) for s in suites)
failed = sum(int(s.get('failures',0))+int(s.get('errors',0)) for s in suites)
counts = Counter(r['estado'] for r in rows)
doc = Document()
sec = doc.sections[0]
sec.page_width,sec.page_height=Inches(8.27),Inches(11.69)
sec.top_margin,sec.bottom_margin=Inches(.72),Inches(.68)
sec.left_margin,sec.right_margin=Inches(.8),Inches(.8)
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Caption']:
    st=doc.styles[name]
    st.font.name='Calibri'
    st.font.color.rgb=RGBColor(0,0,0)
    st.font.size=Pt(10.5 if name=='Normal' else 12)
    st.paragraph_format.space_after=Pt(7)
    st.paragraph_format.line_spacing=1.12
for name,size in [('Title',25),('Heading 1',17),('Heading 2',12),('Subtitle',12),('Caption',9)]:
    doc.styles[name].font.size=Pt(size)
doc.styles['Heading 1'].paragraph_format.space_before=Pt(0)
doc.styles['Heading 2'].paragraph_format.space_before=Pt(8)
footer=sec.footer.paragraphs[0]
footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
run=footer.add_run('Avance 7  |  ')
run.font.size=Pt(9)
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');footer._p.append(fld)

def para(text,style=None):
    return doc.add_paragraph(text,style)

def heading(text): doc.add_heading(text,2)
def page(title):
    doc.add_page_break()
    doc.add_heading(title,1)
def table(headers,data,widths=None):
    t=doc.add_table(rows=1, cols=len(headers))
    t.alignment=WD_TABLE_ALIGNMENT.CENTER
    t.autofit=False
    for i,h in enumerate(headers): t.rows[0].cells[i].text=str(h)
    for row in data:
        cells=t.add_row().cells
        for c,text in zip(cells,row): c.text=str(text)
    for ri,row in enumerate(t.rows):
        for ci,c in enumerate(row.cells):
            if widths: c.width=Inches(widths[ci])
            c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            pr=c._tc.get_or_add_tcPr()
            borders=OxmlElement('w:tcBorders')
            for side in ['top','left','bottom','right']:
                b=OxmlElement('w:'+side);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'D9D9D9');borders.append(b)
            pr.append(borders)
            shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'DCE6EF' if ri==0 else ('F4F6F8' if ri%2==0 else 'FFFFFF'));pr.append(shade)
            margins=OxmlElement('w:tcMar')
            for side in ['top','bottom','left','right']:
                e=OxmlElement('w:'+side);e.set(qn('w:w'),'75');e.set(qn('w:type'),'dxa');margins.append(e)
            pr.append(margins)
            for par in c.paragraphs:
                par.paragraph_format.space_after=Pt(2)
                par.paragraph_format.space_before=Pt(2)
                for r in par.runs:r.font.size=Pt(9);r.bold=(ri==0)
        cant=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(cant)
    repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
    doc.add_paragraph().paragraph_format.space_after=Pt(0)
    return t

def fmt(value,digits=3): return 'No medido' if value=='' else f'{float(value):.{digits}f}'

doc.add_heading('Experimentos preliminares de Bin Packing 1D',0)
para('Avance 7 y preparación de la segunda entrega','Subtitle')
para('Proyecto de Algoritmos Avanzados — 6 de noviembre de 2026')
heading('Resumen de resultados')
para(f'El sistema integra la carga o generación de instancias, validación, ejecución de FFD, BFD y búsqueda exacta, verificación de soluciones y registro de métricas. La evaluación produjo {len(rows)} registros sobre {len(instances)} instancias: {counts["ok"]} soluciones verificadas y {counts["omitido_por_tamano"]} omisiones deliberadas del exacto por tamaño. Las {tests} pruebas automatizadas terminaron con {failed} fallos o errores.')
para('En las familias aleatorias pequeñas ensayadas, ambas heurísticas coincidieron con el óptimo certificado. Sin embargo, el caso [6, 5, 3, 2, 2, 2] con capacidad 10 requirió tres discos con FFD y BFD y solo dos con el exacto. Este resultado muestra que rapidez y optimalidad deben evaluarse por separado.')
heading('Objetivo y alcance')
para('El objetivo es disponer de una implementación funcional y de evidencia reproducible para comparar las alternativas de asignación de archivos a discos. Se minimiza el número de discos de capacidad fija, asignando cada archivo exactamente una vez y sin dividirlo. Los tamaños se interpretan en una unidad común.')
heading('Flujo integrado')
for text in ['1  Cargar un JSON o generar tamaños con una semilla local.',
             '2  Rechazar datos inválidos antes de ejecutar los algoritmos.',
             '3  Ejecutar las tres alternativas con control de tamaño y tiempo para el exacto.',
             '4  Verificar conservación de archivos y capacidades de cada solución.',
             '5  Exportar métricas, soluciones, resúmenes y gráficos para su revisión.']:
    para(text)
para('La carpeta results/avance7 reúne las entradas, las salidas y la configuración utilizadas. El manual de instalación y ejecución se encuentra en README.md; la bitácora y la lista de evidencias se encuentran en docs/.')

page('1 Diseño de los experimentos')
para('Se utilizaron instancias sintéticas enteras y casos de control. La generación emplea random.Random con semilla local, por lo que no altera el estado aleatorio global. Todas las alternativas reciben los mismos datos y las entradas quedan guardadas para repetir las pruebas.')
table(['Elemento','Configuración ejecutada'],[
['Capacidad de las familias','100 unidades por disco'],
['Tamaños n',', '.join(map(str,env['tamanos']))],
['Semillas',', '.join(map(str,env['semillas']))],
['Repeticiones',str(env['repeticiones'])+' por instancia y algoritmo'],
['Uniforme','Enteros en [1, 100]'],['Archivos pequeños','Enteros en [1, 25]'],
['Archivos grandes','Enteros en [51, 100]'],
['Casos de control','Vacío, decimales y contraejemplo de seis archivos'],
['Control del exacto',f'n máximo {env["exact_max"]}; {env["timeout"]} segundos por corrida']], [1.8,4.8])
para('La matriz comprende 63 instancias aleatorias y tres controles. Las tres repeticiones sobre una misma semilla miden variación de ejecución y no representan nuevas muestras independientes. Se mantuvo el orden FFD, BFD y exacto, sin calentamiento previo ni aleatorización de ese orden.')
heading('Métricas y criterios')
para('El tiempo se mide con perf_counter_ns y se expresa en milisegundos. La memoria pico se obtiene con tracemalloc en una ejecución separada: mide asignaciones rastreadas de Python y no la memoria total del proceso. La verificación queda fuera del tiempo del algoritmo, aunque la validación interna forma parte de este.')
para('La calidad se expresa mediante número de discos, desperdicio kC − suma de tamaños y utilización suma de tamaños / (kC). La cota inferior de volumen es el techo de suma de tamaños / C. La brecha porcentual es 100(k − OPT)/OPT y solo se registra si la búsqueda exacta certifica OPT. Para la entrada vacía se establece utilización 1 y brecha 0 por convenio.')
heading('Entorno registrado')
para(f'Python {env["python"].split()[0]}; {env["plataforma"]}. Procesador reportado: {env["procesador"]}. La fecha de la corrida y las versiones instaladas se conservan en entorno.json y dependencias.txt. Los tiempos pueden cambiar con la carga y el equipo.')

page('2 Resultados de tiempo y escala')
para('La tabla muestra la mediana de nueve corridas por familia y tamaño, correspondientes a tres semillas y tres repeticiones. Los valores describen esta muestra; no se presentan como una comparación estadística concluyente.')
data=[]
for fam in ['uniforme','pequenos','grandes']:
    for n in [20,1000]:
        group={r['algoritmo']:r for r in summary if r['familia']==fam and int(r['n'])==n}
        data.append([fam,n,fmt(group['FFD']['tiempo_mediana_ms']),fmt(group['BFD']['tiempo_mediana_ms']),fmt(group['Exacto']['tiempo_mediana_ms']) if n==20 else 'Omitido'])
table(['Familia','n','FFD ms','BFD ms','Exacto ms'],data,[1.65,.55,1.35,1.35,1.7])
doc.add_picture(str(OUT/'tiempos.png'),width=Inches(6.6))
para('Figura 1  Mediana del tiempo de ejecución por familia y tamaño en escalas logarítmicas. El exacto solo se ejecutó hasta n igual a 20.','Caption')
heading('Tendencias observadas')
para('Con 1000 archivos uniformes, FFD resultó más rápido que BFD en esta corrida. FFD deja de explorar al encontrar el primer disco factible, mientras que BFD revisa todos los discos para seleccionar el de menor espacio residual. En la familia de archivos grandes no cabe ningún par, por lo que ambos recorren progresivamente muchos discos y terminan con un disco por archivo.')
para('Los archivos pequeños permiten llenar pocos discos y reducen la cantidad de posiciones que se exploran en comparación con los archivos grandes. En n igual a 20, el exacto para archivos pequeños fue más lento que en las otras dos familias, consistente con la existencia de más combinaciones factibles que debe descartar. Las diferencias de microsegundos requieren más repeticiones para establecer comparaciones estables.')

page('3 Calidad y verificación de soluciones')
para('Las 513 corridas completadas superaron la verificación de multiplicidades y capacidad. Hubo 117 corridas exactas certificadas y ninguna alcanzó el límite temporal. Las 81 omisiones corresponden a los tamaños 100, 300 y 1000, para los que no se ejecutó la búsqueda exacta.')
heading('Caso que separa heurísticas y óptimo')
table(['Alternativa','Discos','Asignación','Brecha'],[
['FFD','3','[6, 3]  [5, 2, 2]  [2]','50 %'],
['BFD','3','[6, 3]  [5, 2, 2]  [2]','50 %'],
['Exacto','2','[6, 2, 2]  [5, 3, 2]','0 %']], [1.0,.65,3.95,1.0])
para('La suma es 20 y la capacidad es 10; la cota inferior es dos discos. La solución exacta alcanza esa cota y prueba su optimalidad. Las heurísticas ubican primero 6 y 3 juntos y dejan al final un archivo de tamaño 2 que necesita otro disco.')
doc.add_picture(str(OUT/'calidad.png'),width=Inches(5.8))
para('Figura 2  Número de discos en el contraejemplo verificado.','Caption')
heading('Condiciones de ventaja y limitaciones')
para('La búsqueda exacta aporta certificación de optimalidad y sirve como referencia para instancias pequeñas, pero su crecimiento combinatorio limita la escala. FFD y BFD resultan prácticas cuando interesa obtener pronto una solución factible. En esta muestra no se observó una ventaja de BFD en número de discos respecto de FFD; no se concluye que sean equivalentes en general.')
para('Con 1000 archivos, la utilización media fue cercana a 98,66 % para uniformes, 99,68 % para pequeños y 75,27 % para grandes en ambas heurísticas. En la última familia cada archivo supera media capacidad: usar n discos es inevitable, aunque quede espacio libre. Para los casos grandes de las otras familias no se dispone de óptimo experimental certificado y su brecha se deja sin valor.')

page('4 Análisis teórico y módulos')
heading('Complejidad de las implementaciones')
table(['Alternativa','Tiempo en peor caso','Espacio auxiliar'],[
['FFD','O(n log n + n²) = O(n²)','O(n)'],
['BFD','O(n log n + n²) = O(n²)','O(n)'],
['Exacto con poda','Combinatorio; cota conservadora O(n^n)','O(n²)']], [1.35,3.6,1.65])
para('FFD y BFD ordenan los archivos y recorren una lista de discos. Las cargas acumuladas permiten comprobar cada candidato en tiempo constante. Hasta n discos pueden inspeccionarse por cada archivo, de donde surge el término cuadrático. Las listas de tamaños, cargas y solución ocupan espacio lineal.')
para('El exacto recorre asignaciones mediante búsqueda en profundidad, usa FFD como mejor solución inicial y elimina ramas que no pueden mejorarla. También evita repetir discos con cargas iguales. Una cota conservadora de hojas es n^n; la poda reduce el trabajo observado, pero no elimina el peor caso combinatorio. La profundidad, la solución y las cargas son lineales, pero los conjuntos de cargas visitadas de los niveles activos pueden acumular O(n²) elementos. El límite temporal interrumpe la búsqueda y no devuelve una solución parcial como óptima.')
para('El crecimiento observado de las heurísticas con n concuerda cualitativamente con la exploración de discos. Las mediciones pequeñas no permiten ajustar una ley asintótica ni demostrar una complejidad. El comportamiento rápido del exacto en ciertos casos refleja la estructura de las instancias y la poda, no una garantía de escalabilidad.')
heading('Responsabilidad de los módulos')
table(['Módulo','Responsabilidad'],[
['src/main.py','Interfaz CLI, selección de entrada y exportación individual'],
['src/generator.py','Generación reproducible y familias de tamaños'],
['src/validation.py','Validación de entrada y verificación de factibilidad'],
['src/algorithms/approximate.py','First Fit Decreasing y Best Fit Decreasing'],
['src/algorithms/exact.py','Búsqueda exacta, poda y control temporal'],
['src/experiments.py','Protocolo, métricas, resúmenes y gráficos'],
['tests/','Pruebas unitarias, oráculo e integración'],
['scripts/generar_informe.py','Generación del informe desde las evidencias']], [2.55,4.05])

page('5 Instalación y reproducción')
heading('Instalación y comandos')
para('Se requiere Python 3.10 o superior. Desde la raíz del proyecto, crear un entorno virtual e instalar las dependencias. En PowerShell se utilizan los siguientes comandos; python debe estar disponible en PATH.')
for cmd in ['python -m venv .venv',r'.venv\Scripts\Activate.ps1','python -m pip install -r requirements.txt',
            'python -m src.main --entrada examples/instancia.json --salida results/manual',
            'python -m src.main --experimentos --timeout 0.2',
            'python -m pytest -q --junitxml=results/avance7/pruebas.xml']:
    par=para(cmd)
    for run in par.runs: run.font.name='Consolas';run.font.size=Pt(9)
para('Para regenerar el informe: instalar requirements-report.txt y ejecutar python scripts/generar_informe.py. La ejecución individual también admite --n, --capacidad, --semilla y --familia. --salida cambia la carpeta de resultados; --repeticiones, --exact-max y --timeout controlan el protocolo. El valor predeterminado de timeout es 1 segundo; la evidencia entregada utiliza 0,2 segundos.')
heading('Entrada y salida')
para('El formato mínimo de entrada es un objeto JSON con capacidad y archivos. Ejemplo: {"capacidad":10,"archivos":[6,5,3,2,2,2]}. El campo id es opcional. La capacidad debe ser positiva y finita; cada tamaño debe ser positivo, finito y no superar esa capacidad. Se rechazan booleanos, datos no numéricos y valores imposibles. Se admite una lista vacía.')
para('La salida individual contiene entrada, metricas y soluciones. Cada solución es una lista de discos, y cada disco es una lista de tamaños. Los errores de entrada producen un mensaje y código de salida 2. Para evitar imprecisiones de decimales binarios se recomienda expresar tamaños y capacidad en una unidad entera común.')
heading('Organización de los resultados')
table(['Archivo en results/avance7','Contenido'],[
['metricas.csv y resumen.csv','Registros completos y agregados por familia, n y algoritmo'],
['instancias.json y soluciones.json','Entradas y soluciones de la primera repetición'],
['entorno.json y dependencias.txt','Equipo, configuración y versiones de paquetes'],
['tiempos.png y calidad.png','Gráficos iniciales de rendimiento y calidad'],
['pruebas.xml','Resultado automatizado en formato JUnit']], [2.8,3.8])
para('Los estados son ok, limite_de_tiempo y omitido_por_tamano. Un campo no disponible se conserva vacío. Para reproducir los discos utilizados deben mantenerse las instancias; para comparar tiempos deben mantenerse también entorno y configuración. No ejecutar procesos simultáneos que escriban en la misma carpeta.')

page('6 Pruebas y bitácora de correcciones')
heading('Pruebas automatizadas')
para(f'La suite final contiene {tests} pruebas aprobadas y {failed} fallos o errores. Conserva las seis pruebas originales y añade validación de datos, conservación de archivos duplicados, inmutabilidad de entradas, generación reproducible, carga JSON, interfaz CLI, estados de omisión y límite temporal, y ejecución completa con CSV, JSON y gráficos.')
para('Una prueba adicional de optimalidad compara el exacto con un oráculo independiente que enumera asignaciones a discos etiquetados. Se cubren las 70 combinaciones con repetición de cuatro tamaños elegidos entre 1 y 5, con capacidad 5. Esta evidencia ayuda a detectar errores de poda; no sustituye un argumento general de corrección.')
heading('Bitácora del 6 de noviembre de 2026')
table(['Hallazgo','Corrección y evidencia'],[
['Validación parcial del prototipo','Validación compartida y verificación para los tres algoritmos'],
['Exacto descrito como programación dinámica','Documentado como búsqueda con poda e incumbente FFD'],
['Sumas repetidas dentro de heurísticas','Cargas acumuladas en FFD y BFD'],
['Generador alteraba random global','Instancia local de Random y rangos explícitos'],
['Ausencia de un protocolo persistido','CLI experimental y exportación de evidencias'],
['Dependencia Python en requirements','Retirada; requisito del intérprete indicado en el manual'],
['Exclusión global en .gitignore','Incluidas pruebas, ejemplos y documentación en control de versiones']], [2.65,3.95])
para('La bitácora detallada se conserva en docs/BITACORA.md. Las correcciones corresponden a problemas observados en el código y la documentación del repositorio. El grupo debe vincularlas con los comentarios recibidos en las revisiones académicas y añadir los responsables y acuerdos correspondientes.')
heading('Validación de la integración')
para('Se comprobó el flujo de carga JSON, ejecución y escritura de la salida individual, así como el protocolo reducido que genera métricas, resúmenes y gráficos. El contraejemplo verifica que la comparación de calidad no presupone optimalidad de las heurísticas. Los estados de interrupción se prueban de forma controlada sin esperar una corrida larga.')

page('7 Preparación de la segunda entrega')
heading('Evidencias disponibles')
table(['Requisito','Evidencia'],[
['Implementación e integración','Código de algoritmos, validación, generador y CLI'],
['Pruebas automatizadas','tests/ y results/avance7/pruebas.xml'],
['Análisis de complejidad','Sección 4 y README.md'],
['Experimentos preliminares','66 instancias, 594 registros y configuración reproducible'],
['Resultados iniciales','Tablas de resumen, soluciones y dos gráficos'],
['Documentación técnica','Instalación, parámetros, formatos y reproducción en README.md'],
['Bitácora actualizada','docs/BITACORA.md'],
['Organización de la entrega','docs/SEGUNDA_ENTREGA.md y este informe']], [2.15,4.45])
heading('Dificultades pendientes')
para('La evaluación debe ampliarse con más semillas, familias adversarias y tamaños pequeños que tensionen la búsqueda exacta. Ninguna corrida preliminar alcanzó el límite temporal, por lo que su frecuencia real todavía no se caracteriza. Conviene añadir calentamiento, alternar el orden de algoritmos y separar las fuentes de variación antes de formular conclusiones estadísticas.')
para('La memoria reportada corresponde a asignaciones Python y no a RSS. No se ha demostrado optimalidad experimental para las instancias grandes uniformes o pequeñas. Los datos decimales arbitrarios conservan las limitaciones del punto flotante; la unidad entera común debe ser la opción de uso preferida. Tampoco se midieron por separado lectura, validación y escritura, porque la comparación se concentra en los algoritmos.')
heading('Preparación de la exposición')
para('El grupo puede demostrar la carga del ejemplo JSON, el rechazo de un archivo que supere la capacidad, la diferencia entre el contraejemplo heurístico y el óptimo y la organización de las métricas exportadas. Antes de presentar, debe completar los datos académicos e integrantes exigidos por su institución y revisar las observaciones recibidas en los avances previos.')
heading('Conclusión')
para('El Avance 7 incorpora un sistema integrado y una base experimental reproducible. FFD y BFD ofrecen soluciones rápidas y factibles en la escala probada, mientras que el exacto permite certificar el óptimo de instancias pequeñas. Los resultados iniciales muestran que el tamaño y la distribución de archivos influyen en el costo y la utilización; el contraejemplo confirma que una buena solución heurística no garantiza el mínimo número de discos.')

path=ROOT/'docs/Informe_Avance_7.docx'
path.parent.mkdir(exist_ok=True)
for style in doc.styles:
    for border in list(style.element.iter(qn('w:pBdr'))):
        border.getparent().remove(border)
for paragraph in doc.paragraphs:
    for border in list(paragraph._p.iter(qn('w:pBdr'))):
        border.getparent().remove(border)
doc.core_properties.title='Experimentos preliminares de Bin Packing 1D'
doc.core_properties.subject='Avance 7 y preparación de la segunda entrega'
doc.core_properties.author=''
doc.save(path)
print(path)
