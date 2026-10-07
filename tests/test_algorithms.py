"""Pruebas unitarias para los algoritmos de bin packing."""

import pytest
from src.algorithms.approximate import first_fit_decreasing, best_fit_decreasing
from src.algorithms.exact import bin_packing_exacto

def test_ffd_basico():
    archivos = [4, 3, 2.5, 2, 1.5, 1]
    capacidad = 5
    solucion = first_fit_decreasing(archivos, capacidad)
    assert len(solucion) == 3
    for disco in solucion:
        assert sum(disco) <= capacidad

def test_bfd_basico():
    archivos = [4, 3, 2.5, 2, 1.5, 1]
    capacidad = 5
    solucion = best_fit_decreasing(archivos, capacidad)
    assert len(solucion) == 3
    for disco in solucion:
        assert sum(disco) <= capacidad

def test_exacto_basico():
    archivos = [4, 3, 2, 1]
    capacidad = 5
    solucion = bin_packing_exacto(archivos, capacidad)
    assert len(solucion) == 2
    for disco in solucion:
        assert sum(disco) <= capacidad

def test_ffd_vacio():
    assert first_fit_decreasing([], 10) == []

def test_bfd_vacio():
    assert best_fit_decreasing([], 10) == []

def test_exacto_vacio():
    assert bin_packing_exacto([], 10) == []
