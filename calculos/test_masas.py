# -*- coding: utf-8 -*-
"""El reparto de peso y la altura del CG que suponen resortes y frenos salen del presupuesto de masas, y el modelo FEM usa las mismas masas."""
import contextlib
import io
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import masas_cg as G
import masas_modelo as MM

with contextlib.redirect_stdout(io.StringIO()):
    import suspension_delantera as SD
    import suspension_trasera as ST
    import frenos as FR
    import cargas_suspension as C


@pytest.fixture(scope="module")
def presupuesto():
    bat = G.escenarios()["túnel central 30 celdas (1.11 m)"]
    return G.metricas(G.componentes(bat, G.ELECTRONICA["trasera, junto a los motores"]))


def test_masa_explicita_son_474_kg():
    assert abs(MM.total() - 474.0) < 1e-6          # + chasis (~90-99 kg) = 564 kg suspendida de 690 kg


def test_constantes_de_reparto_coinciden_con_el_presupuesto(presupuesto):
    assert abs(SD.DIST_DEL - presupuesto["delante"]) < 0.02
    assert abs((1 - ST.DIST_TRAS) - presupuesto["delante"]) < 0.02
    assert abs((1 - FR.DIST_TRAS) - presupuesto["delante"]) < 0.02


def test_altura_del_cg_coincide_con_el_presupuesto(presupuesto):
    assert abs(ST.H_CG - presupuesto["y"]) < 0.02
    assert abs(FR.H_CG - presupuesto["y"]) < 0.02


def test_modelo_fem_coincide_con_el_presupuesto(presupuesto):
    out = C.evaluar_suspension(C.cargar_vigente())
    cg = out["cg"]
    delante_fem = (G.X_EJE_TRAS - cg[0]) / G.BATALLA
    assert abs(delante_fem - presupuesto["delante"]) < 0.02, (delante_fem, presupuesto["delante"])
    assert abs(cg[1] - presupuesto["y"]) < 0.02, (cg[1], presupuesto["y"])


def test_la_pila_cabe_en_el_tunel():
    """30 celdas de 36 mm + placas = 1.11 m; 130 mm de ancho + caja: entra entre las cubetas (z=+-0.31, ancho 0.46) con holgura positiva."""
    largo = G.CELDAS * G.CELDA_ESPESOR + 0.03
    ancho = G.CELDA_ANCHO + 0.012
    assert largo < 1.15
    assert ancho / 2 < (0.31 - 0.23)
