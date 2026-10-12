# calculos/test_puertas.py
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import puertas as P


def test_eje_de_bisagra_sobre_el_espinazo():
    assert abs(P.EJE_A0[2] - 0.15) < 1e-9
    assert abs(np.linalg.norm(P.EJE_U) - 1) < 1e-9
    assert P.EJE_U[0] > 0.99                 # el eje va casi a lo largo del carro


def test_amortiguador_de_catalogo():
    assert P.FUERZA_NOMINAL in P.CATALOGO_N
    assert P.FUERZA_NOMINAL >= 1.1 * P.fuerza_amortiguador(65.0)     # sostiene 65° con margen
    assert 0.08 <= P.carrera_amortiguador() <= 0.18


def test_esfuerzo_de_manija_razonable():
    # abrir/cerrar la puerta no debe pedir más de ~120 N en la manija en ningún ángulo
    for th in range(0, 66, 5):
        assert abs(P.esfuerzo_manual(float(th))) < 120.0, th


def test_equilibrio_de_momentos_sobre_el_eje():
    # peso + viento + amortiguador no deben dejar momento neto sobre el eje (la bisagra no lo resiste)
    for th in (20.0, 45.0, 65.0):
        est = P.estatica(th)
        tau = sum(np.dot(np.cross(r - P.EJE_A0, f), P.EJE_U) for r, f in est["fuerzas_en_puerta"])
        assert abs(tau) < 1e-6


def test_lc7_es_simetrica_y_tiene_las_tres_estaciones():
    lc = P.lc7()
    assert set(lc) == {"h1L", "h2L", "saL", "h1R", "h2R", "saR"}
    for n in ("h1", "h2", "sa"):
        L, R = lc[n + "L"], lc[n + "R"]
        assert np.allclose([L[0], L[1], -L[2], -L[3], -L[4], L[5]], R)       # espejo en z


def test_lc7_transmite_peso_y_viento_al_chasis():
    lc = P.lc7()
    suma_chasis = (lc["h1L"] + lc["h2L"] + lc["saL"])[:3]
    esperado = np.array([0.0, -P.MASA_PUERTA * P.G * P.FACTOR_BACHE, P.VIENTO_N])
    assert np.allclose(suma_chasis, esperado, atol=1e-6)


def test_el_amortiguador_no_cruza_el_pilar_a():
    assert P._libre_del_pilar(P.PD)


def test_la_bisagra_queda_bajo_la_piel_del_techo():
    # piel exterior de Tripo sobre el espinazo: 1.065 (x=1.55) y 1.109 (x=1.85); el perno debe quedar >= 40 mm abajo
    assert 1.065 - P.punto_eje(1.55)[1] >= 0.040
    assert 1.109 - P.punto_eje(1.85)[1] >= 0.040


def test_la_puerta_abierta_deja_pasar_agachado():
    # el punto más bajo de la puerta real abierta a 65° debe quedar > 1.20 m (se mide, no se supone)
    assert P.punto_mas_bajo_abierto(65.0)[1] > 1.20
