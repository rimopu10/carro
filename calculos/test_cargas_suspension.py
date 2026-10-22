# -*- coding: utf-8 -*-
"""Pruebas de cargas_suspension.py: el reparto de fuerzas cierra y el chasis vigente cumple bajo las cargas reales."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cargas_suspension as C

FS_MIN = 2.0


@pytest.fixture(scope="module")
def modelo():
    return C.evaluar_suspension(C.cargar_vigente())


def test_equilibrio_cierra(modelo):
    """Con 6 apoyos mínimos las reacciones deben ser ~0: cargas del piso + inercia de todas las masas en equilibrio."""
    for nom, r in modelo["casos"].items():
        assert r["residual"] < 1.0, (nom, r["residual"])


def test_cada_rueda_transmite_lo_que_recibe(modelo):
    """La suma de fuerzas de los anclajes de una rueda = fuerza del piso + peso/inercia de su masa no suspendida."""
    pts = C.masas_todas(modelo["miembros"])
    M, cg, I = C.propiedades(pts)
    for nom, r in modelo["casos"].items():
        a0 = C.GV + sum(r["P"].values()) / M
        for w in C.RUEDAS:
            fu = C.M_NOSUSP[w] * (C.GV - a0 - np.cross(r["rb"]["alfa"], C.CENTRO[w] - cg))
            suma = sum(f for (ww, k), f in r["anclajes"].items() if ww == w)
            assert np.linalg.norm(suma - (r["P"][w] + fu)) < 1e-6, (nom, w)


def test_todo_anclaje_tiene_tubo(modelo):
    usados = {n for a, b, s, t in modelo["miembros"] for n in (a, b)}
    assert all(v[0] in usados for v in modelo["nodos"].values())


def test_fuerzas_del_piso_no_negativas(modelo):
    """Ninguna rueda se despega en los casos de diseño (Fz >= 0)."""
    for nom, r in modelo["casos"].items():
        for w in C.RUEDAS:
            assert r["P"][w][1] >= 0.0, (nom, w)


def test_chasis_cumple_con_cargas_de_suspension(modelo):
    """Fluencia (con torsión, von Mises) y pandeo: >= 2.0 en las cargas de servicio S1..S4 y >= 1.5 en los casos raros o combinados
    (S5, S6) y en las cotas de la hiperestaticidad de las bisagras ([axial ..])."""
    for nom, r in modelo["casos"].items():
        req = 2.0 if (nom[:2] in ("S1", "S2", "S3", "S4") and "[axial" not in nom) else 1.5
        assert r["fs_min"] >= req, (nom, r["fs_min"], r["peor"])
        assert min(r["pandeo"].values()) >= req, nom


def test_momentos_cierran_por_rueda(modelo):
    """El envoltorio de fuerzas y momentos de los anclajes (respecto al origen) = el del piso + peso/inercia de la masa no
    suspendida. Falla si un brazo, el amortiguador o el tirante tienen mal el signo o el brazo de palanca."""
    pts = C.masas_todas(modelo["miembros"])
    M, cg, I = C.propiedades(pts)
    for nom, r in modelo["casos"].items():
        a0 = C.GV + sum(r["P"].values()) / M
        for w in C.RUEDAS:
            fu = C.M_NOSUSP[w] * (C.GV - a0 - np.cross(r["rb"]["alfa"], C.CENTRO[w] - cg))
            esperado = np.cross(C.PARCHE[w], r["P"][w]) + np.cross(C.CENTRO[w], fu)
            suma = np.zeros(3)
            for (ww, k), f in r["anclajes"].items():
                if ww == w:
                    p = modelo["nodos"][(w[1], w[0], k)][1]
                    suma += np.cross(p, f) + r["interno"][w]["momentos"][k]
            assert np.linalg.norm(suma - esperado) < 1e-6 * max(1.0, np.linalg.norm(esperado)), (nom, w, suma, esperado)


def test_dist_segmentos_contra_fuerza_bruta():
    """holguras.dist_segmentos debe coincidir con la distancia por muestreo fino (la versión anterior sobreestimaba hasta 0.5 m)."""
    import holguras
    rng = np.random.default_rng(7)
    u = np.linspace(0, 1, 401)
    for _ in range(60):
        p1, q1, p2, q2 = (rng.uniform(0, 0.5, 3) for _ in range(4))
        A = p1 + np.outer(u, q1 - p1)
        B = p2 + np.outer(u, q2 - p2)
        fb = float(np.sqrt(((A[:, None, :] - B[None, :, :]) ** 2).sum(-1)).min())
        d = holguras.dist_segmentos(p1, q1, p2, q2)[0]
        assert d <= fb + 1e-9 and fb - d < 2e-3, (d, fb)
