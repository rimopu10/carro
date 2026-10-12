# -*- coding: utf-8 -*-
"""
¿Qué tubos del chasis cruzan el hueco por donde se entra al carro?
El hueco es el contorno de la puerta de gaviota (CONTORNO_LADO de tripo_gaviota.py, el mismo
trazado sobre la piel de Tripo) encogido MARGEN mm, entre el espinazo (|z|=150) y el estribo
(|z|=620, cara interior del riel). Un tubo que lo atraviesa estorba al entrar/salir.

    python calculos/hueco_puerta.py
"""
import json, os
import numpy as np
from matplotlib.path import Path

HERE = os.path.dirname(os.path.abspath(__file__))
CONTORNO_LADO = [(1220, 280), (1220, 740), (1250, 780), (1580, 1040), (1620, 1400),
                 (2080, 1400), (2100, 1060), (2230, 800), (2210, 600), (2150, 450),
                 (2060, 330), (2000, 280)]
Z_MIN, Z_MAX = 0.15, 0.62        # entre espinazo y riel del estribo
X_MAX = 1.97                     # el arco principal (x=2.02) es el borde trasero de la entrada
MARGEN = 0.040                   # m que se encoge el contorno (el pilar A queda en el borde)


def poligono_encogido(m=MARGEN):
    P = np.array(CONTORNO_LADO, float) / 1000.0
    c = P.mean(axis=0)
    # encogido por desplazamiento radial simple (el contorno es casi convexo)
    d = P - c
    n = np.linalg.norm(d, axis=1, keepdims=True)
    return c + d * (1 - m / n)


def tubos_en_hueco(tubos, paso=0.01):
    poly = Path(poligono_encogido())
    res = []
    for t in tubos:
        a, b = np.array(t["a"]), np.array(t["b"])
        L = np.linalg.norm(b - a)
        n = max(int(L / paso), 2)
        P = a + (b - a) * np.linspace(0, 1, n)[:, None]
        dentro = poly.contains_points(P[:, [0, 1]]) & (np.abs(P[:, 2]) > Z_MIN) & (np.abs(P[:, 2]) < Z_MAX) & (P[:, 0] < X_MAX)
        if dentro.any():
            res.append((t["nom"], dentro.mean() * L, (P[dentro].mean(axis=0))))
    return sorted(res, key=lambda r: -r[1])


if __name__ == "__main__":
    ch = json.load(open(os.path.join(HERE, "..", "cad", "chasis.json"), encoding="utf-8"))
    r = tubos_en_hueco(ch["tubos"])
    print("hueco de puerta (contorno encogido %d mm), |z| %.2f-%.2f m" % (MARGEN * 1000, Z_MIN, Z_MAX))
    if not r:
        print("  LIBRE: ningún tubo cruza el hueco")
    for nom, L, p in r:
        print(f"  {nom:18s} {L*1000:6.0f} mm dentro   centro ({p[0]:.2f}, {p[1]:.2f}, {p[2]:+.2f})")
