"""Pruebas para la interfaz CLI y el selector de algoritmos."""
import io
import json
import pytest
from src.main import main
from src.cli import alternar_algoritmo, resolver_con_algoritmo, iniciar_interfaz_cli

def test_cli_argumento_ffd(tmp_path):
    salida = tmp_path / "salida_ffd"
    main(['--algoritmo', 'ffd', '--salida', str(salida)])
    resultado = json.loads((salida / 'ejecucion.json').read_text(encoding='utf-8'))
    assert 'FFD' in resultado['soluciones']
    assert 'BFD' not in resultado['soluciones']
    assert len(resultado['metricas']) == 1
    assert resultado['metricas'][0]['algoritmo'] == 'FFD'

def test_cli_argumento_bfd(tmp_path):
    salida = tmp_path / "salida_bfd"
    main(['-a', 'bfd', '--salida', str(salida)])
    resultado = json.loads((salida / 'ejecucion.json').read_text(encoding='utf-8'))
    assert 'BFD' in resultado['soluciones']
    assert 'FFD' not in resultado['soluciones']
    assert len(resultado['metricas']) == 1
    assert resultado['metricas'][0]['algoritmo'] == 'BFD'

def test_alternar_algoritmo():
    # Ciclo FFD ↔ BFD
    assert alternar_algoritmo('FFD') == 'BFD'
    assert alternar_algoritmo('BFD') == 'FFD'
    # Desde AMBOS o Exacto vuelve a FFD (punto de entrada del ciclo)
    assert alternar_algoritmo('AMBOS') == 'FFD'
    assert alternar_algoritmo('Exacto') == 'FFD'

def test_resolver_con_algoritmo():
    res_ffd = resolver_con_algoritmo('FFD', [4, 3, 2, 1], 5)
    assert res_ffd['estado'] == 'ok'
    assert res_ffd['discos'] == 2

    res_bfd = resolver_con_algoritmo('BFD', [4, 3, 2, 1], 5)
    assert res_bfd['estado'] == 'ok'
    assert res_bfd['discos'] == 2

def test_interfaz_interactiva_flujo(monkeypatch):
    # Simula entrada de usuario: 1 (cambiar a BFD), 4 (ejecutar), 5 (comparar), 0 (salir)
    entradas = iter(['1', '4', '5', '0'])
    monkeypatch.setattr('builtins.input', lambda prompt='': next(entradas))
    iniciar_interfaz_cli()
