"""Pruebas de integración, validación y optimalidad con oráculo independiente."""
import itertools
import json
import random
import pytest
from src.algorithms.approximate import first_fit_decreasing, best_fit_decreasing
from src.algorithms.exact import bin_packing_exacto
from src.validation import verificar_solucion
from src.generator import generar_instancia
from src.experiments import cargar_instancia, ejecutar_instancia, ejecutar_experimentos
from src.main import main

ALGS = [first_fit_decreasing, best_fit_decreasing, bin_packing_exacto]

@pytest.mark.parametrize('alg', ALGS)
@pytest.mark.parametrize('items,cap', [([11],10),([0],10),([-1],10),([True],10),([float('nan')],10),([float('inf')],10),([1],0),([1],float('nan')),([1],True),('123',10)])
def test_rechazo(alg,items,cap):
    with pytest.raises(ValueError): alg(items,cap)

@pytest.mark.parametrize('sol', [[[4]],[[4,4,2]],[[4,2,2]],[[4,2],[]]])
def test_salida_invalida(sol):
    with pytest.raises(ValueError): verificar_solucion([4,2],5,sol)

def oracle(items,cap):
    # Enumeración independiente de asignaciones a k discos etiquetados.
    for k in range(1,len(items)+1):
        for etiquetas in itertools.product(range(k),repeat=len(items)):
            cargas = [0]*k
            for x,i in zip(items,etiquetas): cargas[i] += x
            if max(cargas) <= cap: return k
    return 0

def test_exacto_con_oraculo():
    for items in itertools.combinations_with_replacement(range(1,6),4):
        sol = bin_packing_exacto(list(items),5)
        verificar_solucion(list(items),5,sol)
        assert len(sol) == oracle(items,5)

@pytest.mark.parametrize('alg', ALGS)
def test_no_modifica_y_duplicados(alg):
    items=[2,2,2,2,1,1]
    original=items[:]
    verificar_solucion(items,5,alg(items,5))
    assert items == original

def test_contraejemplo():
    data={'archivos':[6,5,3,2,2,2],'capacidad':10}
    filas,sol = ejecutar_instancia(data)
    assert [len(sol[n]) for n in ('FFD','BFD','Exacto')] == [3,3,2]
    assert [r['brecha_opt_pct'] for r in filas] == [50,50,0]

def test_reproducibilidad_y_random_global():
    estado=random.getstate()
    assert generar_instancia(10,100,42) == generar_instancia(10,100,42)
    assert estado == random.getstate()
    for c in [1,2,5,100]:
        for f in ['uniforme','pequenos','grandes']:
            assert all(0 < x <= c for x in generar_instancia(10,c,42,f))

@pytest.mark.parametrize('n,c', [(-1,10),(1.5,10),(True,10),(1,0),(1,2.5)])
def test_generador_invalido(n,c):
    with pytest.raises(ValueError): generar_instancia(n,c)

def test_omitido_y_timeout(monkeypatch):
    import src.experiments as exp
    filas,_ = ejecutar_instancia({'archivos':[2,2], 'capacidad':5},exact_max=1)
    assert filas[-1]['estado']=='omitido_por_tamano'
    def lento(*args,**kw): raise TimeoutError()
    monkeypatch.setitem(exp.ALGORITMOS,'Exacto',lento)
    filas,_ = ejecutar_instancia({'archivos':[2,2], 'capacidad':5})
    assert filas[-1]['estado']=='limite_de_tiempo'
    assert filas[0]['brecha_opt_pct'] is None

def test_limite_exacto_real(monkeypatch):
    import src.algorithms.exact as exact
    reloj=iter([0,2])
    monkeypatch.setattr(exact,'perf_counter',lambda:next(reloj))
    with pytest.raises(TimeoutError): exact.bin_packing_exacto([1],5,limite_segundos=1)

def test_json_y_cli(tmp_path):
    entrada=tmp_path/'entrada.json'
    entrada.write_text(json.dumps({'archivos':[2,3],'capacidad':5}),encoding='utf-8')
    assert cargar_instancia(entrada)['archivos']==[2,3]
    main(['--entrada',str(entrada),'--salida',str(tmp_path/'salida')])
    assert json.loads((tmp_path/'salida/ejecucion.json').read_text(encoding='utf-8'))['metricas'][0]['verificado']
    entrada.write_text('{}',encoding='utf-8')
    with pytest.raises(ValueError): cargar_instancia(entrada)

def test_protocolo_completo(tmp_path):
    filas=ejecutar_experimentos(tmp_path,tamanos=(4,),semillas=(11,),repeticiones=1)
    assert len(filas)==18
    assert all(f['verificado'] for f in filas)
    for name in ['metricas.csv','resumen.csv','instancias.json','soluciones.json','entorno.json','tiempos.png','calidad.png']:
        assert (tmp_path/name).stat().st_size > 0
