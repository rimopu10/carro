# -*- coding: utf-8 -*-
"""
Verificación numérica de la carrocería v3 contra la ingeniería. Sin ojímetro.

Mide, sobre el STL exportado (la superficie subdividida real, no la jaula):
  1. cada tubo del chasis (cad/chasis.json) contra la piel: distancia del eje a la
     superficie menos el radio del tubo, con signo (negativo = el tubo asoma o cae en
     un pozo de rueda);
  2. las cuatro llantas: ningún vértice de la piel dentro de la llanta + 30 mm;
  3. la cabeza del maniquí (1.958, 0.862, ±0.31, r=0.104) contra el techo interior;
  4. que el STL sea un sólido cerrado (imprimible).

Nació de la auditoría del 2026-09-05, que encontró que la verificación anterior sólo
comparaba la altura del centro del techo y se le escapaban las esquinas del arco.

Correr:  python calculos/verificar_piel_v3.py      (necesita trimesh + rtree)
"""
import json
import os
import sys

import numpy as np
import trimesh
from trimesh.proximity import ProximityQuery

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(HERE, "..")
SANDWICH = 0.012        # espesor del cascarón: menos aire que esto = el tubo está EN la piel
MARGEN = 0.020          # aire deseado sobre el tubo (aviso por debajo)


def main():
    piel = trimesh.load(os.path.join(RAIZ, "cad", "carro-v3-carroceria-mm.stl"))
    piel.apply_scale(0.001)
    ch = json.load(open(os.path.join(RAIZ, "cad", "chasis.json"), encoding="utf-8"))
    pq = ProximityQuery(piel)

    edges = piel.edges_sorted
    _, cnt = np.unique(edges, axis=0, return_counts=True)
    print(f"STL  {len(piel.faces)} triangulos · cerrado={'SI' if piel.is_watertight else 'NO'} "
          f"({(cnt == 1).sum()} aristas de borde, {(cnt > 2).sum()} con >2 caras) · "
          f"volumen {piel.volume:.3f} m3")

    print(f"\n1. TUBOS vs PIEL  (aire = distancia eje->piel - radio; CONFLICTO si "
          f"< {SANDWICH*1000:.0f} mm [el tubo cae en el sándwich], aviso si < {MARGEN*1000:.0f})")
    filas = []
    for t in ch["tubos"]:
        a, b = np.array(t["a"]), np.array(t["b"])
        r = (t["sec"].get("d") or t["sec"].get("b")) / 2.0
        pts = a + (b - a)[None, :] * np.linspace(0, 1, 11)[:, None]
        d = pq.signed_distance(pts)                # trimesh: + = dentro del sólido
        k = int(np.argmin(d))
        filas.append((d.min() - r, t["nom"], d.min(), r, pts[k]))
    filas.sort()
    malos = [f for f in filas if f[0] < SANDWICH]
    avisos = [f for f in filas if SANDWICH <= f[0] < MARGEN]
    print(f"   {'tubo':16s}{'aire mm':>9}{'eje->piel':>11}{'radio':>7}   punto peor")
    for m, nom, dmin, r, p in (malos or filas[:5]):
        print(f"   {nom:16s}{m*1000:>+9.1f}{dmin*1000:>11.1f}{r*1000:>7.1f}   "
              f"({p[0]:.2f}, {p[1]:.2f}, {p[2]:+.2f})")
    print(f"   -> {len(malos)} tubos en CONFLICTO de {len(filas)}; {len(avisos)} con aire entre "
          f"{SANDWICH*1000:.0f} y {MARGEN*1000:.0f} mm (piso y espinazo: por diseño van a 16 mm)")

    print("\n2. LLANTAS vs PIEL")
    V = piel.vertices
    for w in ch["ruedas"]:
        dz = np.abs(V[:, 2] - w["z"]) <= w["W"] / 2 + 0.030
        rr = np.hypot(V[:, 0] - w["x"], V[:, 1] - w["R"])
        dentro = int((dz & (rr <= w["R"] + 0.030)).sum())
        print(f"   rueda x={w['x']:.2f} z={w['z']:+.3f}: {dentro} vertices de piel en llanta+30mm, "
              f"holgura radial minima {(rr[dz] - w['R']).min()*1000:.0f} mm")

    print("\n3. CABEZA DEL PILOTO (1.75 m) vs TECHO")
    for z in (0.31, -0.31):
        d = pq.signed_distance([[1.958, 0.862, z]])[0]
        print(f"   z={z:+.2f}: claro sobre la cabeza {(d - 0.104)*1000:.0f} mm")

    ok = not malos and piel.is_watertight
    print("\nVEREDICTO:", "OK" if ok else "HAY CONFLICTOS (arriba)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
