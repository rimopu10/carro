# -*- coding: utf-8 -*-
"""
ESPACIOS LIBRES BAJO LA PIEL: ¿dónde cabe una cajuela delantera (frunk), los líquidos y servicios, y el maletero trasero?

Interior de la piel de Tripo (cad/_vista/tripo-cerrado-sin-ruedas-mm.stl, con cascarón de 12 mm + 20 mm de holgura) MENOS: tubos del chasis, ruedas con su
recorrido, brazos/amortiguadores/tirantes/cremallera, columna de dirección, pies y piernas de piloto y pasajero (incluida la posición de riel adelantada),
la pila de la batería y la electrónica trasera. Rejilla de 5 cm; se busca la caja alineada a los ejes y simétrica respecto a z=0 de mayor volumen que quepa en cada zona.

    python calculos/espacios_libres.py
"""
import contextlib
import io
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
with contextlib.redirect_stdout(io.StringIO()):
    import buck_piloto as BK
    import cabina_mandos as CM
    import suspension_delantera as SD
    import suspension_trasera as ST
    import cargas_suspension as C
    import masas_cg as G

PASO = 0.05
HOLGURA_PIEL = 0.032          # 12 mm de cascarón + 20 mm de holgura
R_RUEDA_VIAJE = 0.075         # el neumático sube hasta 75 mm en el recorrido


def seg_dist(P, a, b):
    ab = b - a
    t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


def construir(x0, x1, y1, zmax=0.80, y_ini=0.0):
    xs = np.arange(x0, x1, PASO) + PASO / 2
    ys = np.arange(y_ini, y1, PASO) + PASO / 2
    zs = np.arange(-zmax, zmax, PASO) + PASO / 2
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
    P = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
    return xs, ys, zs, P


def libre(x0, x1, y1, obst_fn, piel, y_ini=0.0):
    xs, ys, zs, P = construir(x0, x1, y1, y_ini=y_ini)
    dentro = piel.contains(P)
    ok = dentro.copy()
    idx = np.where(dentro)[0]
    # distancia a la piel (sólo de los puntos dentro): se exige >= HOLGURA_PIEL
    if len(idx):
        d = np.abs(trimesh.proximity.closest_point(piel, P[idx])[1])
        ok[idx[d < HOLGURA_PIEL]] = False
    ok &= obst_fn(P)
    return xs, ys, zs, ok.reshape(len(xs), len(ys), len(zs))


def mejor_caja(libre3, xs, ys, zs, minimo=(2, 2, 2)):
    """Caja alineada a los ejes y SIMÉTRICA respecto al plano z=0 (es lo que sirve para una cajuela) de mayor volumen con todas las celdas libres.
    Devuelve (vol m3, (x0,x1),(y0,y1),(z0,z1))."""
    nx, ny, nz = libre3.shape
    mitad = nz // 2
    mejor = (0.0, None)
    for i0 in range(nx):
        for i1 in range(i0 + minimo[0], nx + 1):
            fx = libre3[i0:i1].all(axis=0)                    # (ny, nz)
            for j0 in range(ny):
                col = fx[j0]
                for j1 in range(j0 + minimo[1], ny + 1):
                    col = fx[j0:j1].all(axis=0)               # libre en todo el tramo y para cada z
                    if not col[mitad - 1] or not col[mitad]:
                        break
                    k = 0
                    while mitad - 1 - k >= 0 and mitad + k < nz and col[mitad - 1 - k] and col[mitad + k]:
                        k += 1
                    if 2 * k >= minimo[2]:
                        vol = (i1 - i0) * (j1 - j0) * 2 * k * PASO ** 3
                        if vol > mejor[0]:
                            mejor = (float(vol), ((xs[i0] - PASO / 2, xs[i1 - 1] + PASO / 2), (ys[j0] - PASO / 2, ys[j1 - 1] + PASO / 2),
                                                  (zs[mitad - k] - PASO / 2, zs[mitad + k - 1] + PASO / 2)))
    return mejor


def main():
    piel = trimesh.load(os.path.join(HERE, "..", "cad", "_vista", "tripo-cerrado-sin-ruedas-mm.stl"))
    piel = piel.simplify_quadric_decimation(face_count=12000)      # 681 mil caras -> 12 mil: la precisión necesaria es de centímetros
    piel.apply_scale(0.001)
    with contextlib.redirect_stdout(io.StringIO()):
        mem = C.cargar_vigente()
    F = C.F
    tubos = [(F.NODES[a], F.NODES[b], s["c"]) for a, b, s, t in mem]
    # --- obstáculos comunes -------------------------------------------------------------------------------------------
    caps = []
    for z in (0.31, -0.31):
        for hx in (BK.RIELES[0], BK.NOMINAL["hx"]):
            p = BK.postura(hx, BK.NOMINAL["hy"], BK.NOMINAL["recline"], estatura=1.60 if hx == BK.RIELES[0] else 1.75)
            for c in BK.capsulas(p, z=z):
                caps.append((c["a"], c["b"], c["r"] + 0.05))
        # pedalera: volumen de pedales y mecanismo delante de los pies (hasta el mamparo x=0.35) con holgura
        caps.append((np.array([0.36, 0.20, z]), np.array([0.56, 0.38, z]), 0.12))
    hub = np.array([1.30, 0.58, 0.31])
    columna = [(CM.PINON, np.array([0.73, 0.53, 0.31]), 0.04), (np.array([0.73, 0.53, 0.31]), hub, 0.04)]
    susp = []
    for s_ in (1, -1):
        m = lambda p: np.array([p[0], p[1], s_ * abs(p[2])])
        susp += [(m(SD.LA1), m(SD.LBJ0), 0.05), (m(SD.LA2), m(SD.LBJ0), 0.05), (m(SD.UA1), m(SD.UBJ0), 0.05), (m(SD.UA2), m(SD.UBJ0), 0.05),
                 (m(SD.SHK_SUP), m(SD.SHK_INF0), 0.07), (m(SD.TR0), m(SD.RACK), 0.04)]
    susp.append((np.array([SD.RACK[0], SD.RACK[1], -SD.RACK[2]]), np.asarray(SD.RACK, float), 0.05))

    def cilindro_rueda(P, cx, R, zc, ancho):
        d = np.hypot(P[:, 0] - cx, P[:, 1] - R)
        return (d < R + R_RUEDA_VIAJE + 0.03) & (np.abs(np.abs(P[:, 2]) - zc) < ancho / 2 + 0.05)

    def libre_frente(P):
        ok = np.ones(len(P), bool)
        for a, b, r in tubos:
            ok &= seg_dist(P, a, b) > r + 0.02
        for a, b, r in caps + columna + susp:
            ok &= seg_dist(P, a, b) > r
        ok &= ~cilindro_rueda(P, SD.W0[0], SD.R_RUEDA, SD.W0[2], SD.ANCHO_LLANTA)
        return ok

    pila = (1.05 - 0.03, 2.16 + 0.03, 0.17, 0.42, 0.085)

    def libre_atras(P):
        ok = np.ones(len(P), bool)
        for a, b, r in tubos:
            ok &= seg_dist(P, a, b) > r + 0.02
        for s_ in (1, -1):
            m = lambda p: np.array([p[0], p[1], s_ * abs(p[2])])
            for a, b, r in ((m(ST.PIV), m(np.array([ST.EJE0[0], ST.EJE0[1], ST.Z_PUNTA])), 0.06), (m(ST.SHK_SUP), m(ST.SHK_INF0), 0.07)):
                ok &= seg_dist(P, a, b) > r
        ok &= ~cilindro_rueda(P, ST.EJE0[0], ST.R_RUEDA, ST.EJE0[2], 0.30)       # motor de cubo + llanta: ancho ~0.30
        ok &= ~((P[:, 0] > 2.05) & (P[:, 0] < 2.50) & (P[:, 1] < 0.40) & (np.abs(P[:, 2]) < 0.50))   # electrónica de potencia (15 kg) junto a los motores
        return ok

    res = {}
    modo = sys.argv[1] if len(sys.argv) > 1 else "todo"
    todas = {"FRUNK bajo el cofre, nariz (delante del mamparo x<0.36)": (0.0, 0.36, 0.70, libre_frente, 0.10),
             "BANDEJA bajo el cofre, sobre la caja delantera (x 0.36-0.95, y>0.50)": (0.36, 0.95, 0.85, libre_frente, 0.50),
             "HUECO bajo el tablero entre las piernas (no accesible por el cofre)": (0.0, 1.00, 0.85, libre_frente, 0.0),
             "MALETERO (detrás del arco)": (2.04, 3.10, 1.10, libre_atras, 0.0)}
    sel = {k: v for k, v in todas.items() if modo == "todo" or (modo == "frunk" and k.startswith(("FRUNK", "BANDEJA")))}
    for nombre, (x0, x1, y1, fn, y_ini) in sel.items():
        xs, ys, zs, L = libre(x0, x1, y1, fn, piel, y_ini)
        vol_total = L.sum() * PASO ** 3
        v, caja = mejor_caja(L, xs, ys, zs)
        res[nombre] = (vol_total, v, caja)
        print(f"== {nombre}")
        print(f"   volumen libre total {vol_total*1000:.0f} L (con huecos sueltos)")
        if caja:
            (a, b), (c, d), (e, f) = caja
            print(f"   mayor caja libre: {v*1000:.0f} L = {b-a:.2f} (x) × {f-e:.2f} (z) × {d-c:.2f} (y) m   en x {a:.2f}-{b:.2f}, y {c:.2f}-{d:.2f}, z {e:+.2f}-{f:+.2f}")
    return res


if __name__ == "__main__":
    main()
