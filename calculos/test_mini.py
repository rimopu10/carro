# -*- coding: utf-8 -*-
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mini  # noqa: E402


def test_escala_uno_reproduce_la_lista_de_corte_real():
    """Con las secciones reales el generador da los mismos cortes que analisis_chasis.py."""
    ms = mini.leer()
    cs = mini.cortes(ms, lambda e: mini.c_real(e["sec"]) / 1000.0)
    assert len(ms) == 90
    for e, c in zip(ms, cs):
        r = e["real"]
        assert abs(c["L"] * 1000 - float(r["largo_entre_centros_mm"])) < 1.0, r["#"]
        assert abs(c["corte"] * 1000 - float(r["largo_de_corte_mm"])) < 1.0, r["#"]
        assert c["extremos"][0][2] == r["corte_A"], r["#"]
        assert c["extremos"][1][2] == r["corte_B"], r["#"]


def test_la_mini_conserva_la_geometria_a_escala():
    k = 5
    r = mini.generar(k, 1000)
    reales = {(e["a"], e["b"]): np.linalg.norm(e["pb"] - e["pa"]) * 1000 for e in mini.leer()}
    for f in r["filas"]:
        assert abs(f["largo_centros_mm"] * k - reales[(f["de"], f["a"])]) < 1.0


def test_barras_no_se_pasan_y_cada_pieza_va_una_vez():
    r = mini.generar(5, 1000)
    usadas = [p for b in r["barras"] for p, _ in b["piezas"]]
    assert len(usadas) == len(set(usadas))
    for b in r["barras"]:
        assert b["resta"] >= 0
    assert abs(sum(l for b in r["barras"] for _, l in b["piezas"]) - r["total_mm"]) < 1e-6


def test_distancia_segmentos():
    a, b = np.array([0., 0, 0]), np.array([1., 0, 0])
    assert abs(mini.distancia_segmentos(a, b, np.array([0.5, 1, 0]), np.array([0.5, 1, 1])) - 1.0) < 1e-9
    assert abs(mini.distancia_segmentos(a, b, np.array([2., 0, 0]), np.array([3., 0, 0])) - 1.0) < 1e-9
