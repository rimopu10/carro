# -*- coding: utf-8 -*-
"""
Verifica el chasis (cad/chasis.json) contra la piel de Tripo (cad/carroceria-tripo-solida-mm.stl).

La piel de Tripo es un sólido cuya cabina está vacía bajo un techo delgado, y trae sus propias
ruedas (generadas con IA, se van a rehacer). Por eso no sirve la distancia con signo de
verificar_piel_v3.py. Aquí se mide, para cada punto del eje de cada tubo, cuánto aire hay hasta
la piel EXTERIOR en tres direcciones: arriba (+y) y a los lados (±z), con un rayo desde afuera.

    aire = distancia del borde del tubo a la piel exterior - SANDWICH (12 mm de cascarón)

Negativo = el tubo asoma o toca la piel. Cerca de las ruedas el rayo lateral choca con la llanta
de Tripo y sobreestima el aire: esos tubos se marcan con (*).

    python calculos/verificar_piel_tripo.py cad/_vista/tripo-cerrado-sin-ruedas-mm.stl   (se genera con preparar_piel_tripo.py)
(ver cierre en calculos/arreglar_chasis_tripo.py)
"""
import json
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(HERE, "..")
SANDWICH = 0.012
MARGEN = 0.020


def aire_tubo(primer_golpe, a, b, r, n=9):
    """Aire (m) entre el borde del tubo a-b (radio r) y la piel exterior, sin descontar el
    cascarón: el peor de n puntos, hacia arriba y hacia el flanco. -> (aire, punto, 'techo'|'flanco')"""
    mejor = (np.inf, None, "")
    for u in np.linspace(0, 1, n):
        p = a + (b - a) * u
        d = primer_golpe(p + [0, 3.0, 0], [0, -1, 0])
        m_top = (p[1] + 3.0 - d) - (p[1] + r) if np.isfinite(d) else np.inf
        lat = np.inf
        if abs(p[2]) > 0.05:              # sólo el flanco del lado donde está el tubo
            s = 1 if p[2] > 0 else -1
            d = primer_golpe(p + [0, 0, 3.0 * s], [0, 0, -s])
            if np.isfinite(d):
                lat = (abs(p[2]) + 3.0 - d) - (abs(p[2]) + r)
        m = min(m_top, lat)
        if m < mejor[0]:
            mejor = (m, p, "techo" if m_top <= lat else "flanco")
    return mejor


def cargar_piel(ruta):
    piel = trimesh.load(ruta)
    piel.apply_scale(0.001)
    ray = trimesh.ray.ray_triangle.RayMeshIntersector(piel)

    def primer_golpe(origen, dire):
        """Distancia del origen al primer triángulo, o inf."""
        loc, idx, _ = ray.intersects_location([origen], [dire], multiple_hits=False)
        return float(np.linalg.norm(loc[0] - origen)) if len(loc) else np.inf
    return primer_golpe


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "cad", "carroceria-tripo-solida-mm.stl")
    primer_golpe = cargar_piel(ruta)
    ch = json.load(open(os.path.join(RAIZ, "cad", "chasis.json"), encoding="utf-8"))
    ruedas = ch["ruedas"]
    filas = []
    for t in ch["tubos"]:
        r = (t["sec"].get("d") or t["sec"].get("b")) / 2.0
        m, p, donde = aire_tubo(primer_golpe, np.array(t["a"]), np.array(t["b"]), r)
        cerca_rueda = any(abs(p[0] - w["x"]) < w["R"] + 0.05 and abs(abs(p[2]) - abs(w["z"])) < 0.3
                          for w in ruedas)
        filas.append((m - SANDWICH, t["nom"], p, donde, cerca_rueda))

    filas.sort(key=lambda f: f[0])
    malos = [f for f in filas if f[0] < 0]
    print(f"{'tubo':18s}{'aire mm':>9}  {'donde':7s} punto peor (x, y, z)")
    for m, nom, p, donde, cr in filas[:30]:
        print(f"{nom:18s}{m*1000:>+9.1f}  {donde:7s} ({p[0]:.2f}, {p[1]:.2f}, {p[2]:+.2f}){' (*)' if cr else ''}")
    n_av = sum(1 for f in filas if 0 <= f[0] < MARGEN - SANDWICH)
    print(f"\n-> {len(malos)} tubos asoman o tocan la piel de {len(filas)}; {n_av} con menos de "
          f"{(MARGEN - SANDWICH)*1000:.0f} mm de aire extra")


if __name__ == "__main__":
    main()
