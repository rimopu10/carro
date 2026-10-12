# calculos/test_buck_piloto.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import buck_piloto as B


def test_maniqui_es_adulto_real():
    # el maniquí viejo del proyecto tenía 0.41 m cadera->hombro
    assert abs(B.TRONCO - 0.51) < 1e-9


def test_postura_nominal_cumple_el_diseno():
    m = B.metricas(B.postura(1.50, 0.26, 40.0))
    assert m["espalda_barra"] >= 0.030
    assert m["holgura_techo"] >= 0.060       # coronilla vs límite útil del techo
    assert m["nuca_arco"] >= 0.080           # nuca vs cara delantera del arco
    assert m["cabecera_grados"] >= 12.0      # borde inferior de la cabecera sobre el ojo (spec §6)


def test_postura_vieja_no_cabe():
    m = B.metricas(B.postura(1.62, 0.30, 30.0))
    assert m["holgura_techo"] < 0.0          # la coronilla pasa el techo


def test_recorrido_con_pedales_fijos():
    # 1.80 m se sienta donde sus pies alcanzan el mismo pedal: nuca y espalda no tocan el arco
    hx = B.cadera_para_pedal(1.80)
    m = B.metricas(B.postura(hx, 0.26, 40.0, estatura=1.80))
    assert hx > B.NOMINAL["hx"]                    # el alto va más atrás
    assert m["nuca_arco"] >= 0.040
    assert m["espalda_barra"] >= -0.005            # la espalda no toca la barra de cinturones
    assert B.RIELES[0] < B.NOMINAL["hx"] < B.RIELES[1]


def test_1_85_ya_no_cabe_contra_la_barra():
    m = B.metricas(B.postura(B.cadera_para_pedal(1.85), 0.26, 40.0, estatura=1.85))
    assert m["espalda_barra"] < -0.010


def test_1_60_se_sienta_adelante_y_cabe():
    hx = B.cadera_para_pedal(1.60)
    m = B.metricas(B.postura(hx, 0.26, 40.0, estatura=1.60))
    assert hx < B.NOMINAL["hx"]
    assert m["holgura_techo"] > 0.0


def test_capsulas_cubren_piernas_y_cabeza():
    caps = B.capsulas(B.postura(1.50, 0.26, 40.0), z=0.31)
    nombres = {c["nombre"] for c in caps}
    assert {"muslo", "pierna", "pie", "torso", "cabeza"} <= nombres
