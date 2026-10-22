# -*- coding: utf-8 -*-
"""
MANDOS: dónde pueden ir el volante y la columna de dirección sin chocar con el cuerpo ni con los tubos, y si el piloto alcanza.

El piloto va reclinado 40 grados con la cadera a x=1.50 (buck_piloto.py); el volante tiene que caber entre el pecho, los muslos
y las rodillas. La columna recta va del piñón de la cremallera (x~0.43, y~0.37) al cubo del volante. Se barre la posición del
cubo y se pide: aro a >= HOLG_CUERPO de muslo/rodilla/torso, alcance de los brazos entre ALC_MIN y ALC_MAX, columna a >= HOLG_TUBO
de todos los tubos del chasis.

    python calculos/cabina_mandos.py
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import buck_piloto as BK

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ch = json.load(open(os.path.join(HERE, "..", "cad", "chasis.json"), encoding="utf-8"))
TUBOS = [(np.array(t["a"], float), np.array(t["b"], float), (t["sec"].get("d") or t["sec"].get("b")) / 2, t["nom"]) for t in ch["tubos"]]

Z_PIL = 0.31
PINON = np.array([0.43, 0.37, Z_PIL])      # eje del piñón sobre la cremallera (RACK x=0.43, y=0.34)
R_COL = 0.011                              # columna Ø22
HOLG_CUERPO, HOLG_TUBO = 0.06, 0.020
ALC_MIN, ALC_MAX = 0.50, 0.62              # hombro -> agarre del aro (codo ~110-140 grados)
CORTE_ARO = 0.0                            # aro de fondo plano: se corta CORTE_ARO de la parte baja


def dist_seg_seg(p1, q1, p2, q2):
    u, v, w = q1 - p1, q2 - p2, p1 - p2
    a, b, c, d, e = u @ u, u @ v, v @ v, u @ w, v @ w
    D = a * c - b * b
    s = 0.0 if D < 1e-14 else (b * e - c * d) / D
    s = float(np.clip(s, 0, 1))
    t = float(np.clip((b * s + e) / c if c > 1e-14 else 0.0, 0, 1))
    s = float(np.clip((b * t - d) / a, 0, 1)) if a > 1e-14 else 0.0
    return float(np.linalg.norm((p1 + s * u) - (p2 + t * v)))


def aro(centro, eje, radio, n=48):
    """Puntos del aro del volante: circunferencia de radio `radio` en el plano perpendicular a `eje`."""
    e = eje / np.linalg.norm(eje)
    a = np.cross(e, [0, 0, 1.0])
    a /= np.linalg.norm(a)
    b = np.cross(e, a)
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return centro + radio * (np.outer(np.cos(th), a) + np.outer(np.sin(th), b))


def evaluar(hub, d_aro, estatura=1.75, hx=None):
    hx = BK.NOMINAL["hx"] if hx is None else hx
    p = BK.postura(hx, BK.NOMINAL["hy"], BK.NOMINAL["recline"], estatura=estatura)
    caps = BK.capsulas(p, z=Z_PIL)
    eje = hub - PINON                       # el eje del volante sigue la columna (recta)
    P = aro(hub, eje, d_aro / 2)
    if CORTE_ARO:
        P = P[(P[:, 1] - hub[1]) > -(d_aro / 2 - CORTE_ARO)]
    holg_c = min(BK.dist_punto_capsula(P, c).min() for c in caps if c["nombre"] in ("muslo", "pierna", "torso", "cabeza"))
    sh = np.array([p["hombro"][0], p["hombro"][1], Z_PIL])
    # agarre a las 9 y a las 3: puntos del aro a +-radio lateral
    lat = np.cross(eje / np.linalg.norm(eje), [0, 1.0, 0])
    lat /= np.linalg.norm(lat)
    agarre = [hub + s * lat * d_aro / 2 for s in (+1, -1)]
    hombros = [sh + np.array([0, 0, 0.20]), sh - np.array([0, 0, 0.20])]
    alcance = max(np.linalg.norm(agarre[i] - hombros[i]) for i in range(2))
    alcance_min = min(np.linalg.norm(agarre[i] - hombros[i]) for i in range(2))
    # columna contra tubos del chasis (segmento piñón -> cubo)
    holg_t, cual = 9.0, ""
    for a, b, r, nom in TUBOS:
        if min(np.linalg.norm(a - PINON), np.linalg.norm(b - PINON)) < 0.03:
            continue
        d = dist_seg_seg(PINON + 0.04 * (hub - PINON) / np.linalg.norm(hub - PINON), hub, a, b) - r - R_COL
        if d < holg_t:
            holg_t, cual = d, nom
    return dict(holg_cuerpo=holg_c, alcance=alcance, alcance_min=alcance_min, holg_tubo=holg_t, tubo=cual, hub=hub)


def barrido(d_aro, estatura=1.75, hx=None):
    mejores = []
    for x in np.arange(1.05, 1.46, 0.02):
        for y in np.arange(0.50, 0.86, 0.02):
            r = evaluar(np.array([x, y, Z_PIL]), d_aro, estatura, hx)
            ok = (r["holg_cuerpo"] >= HOLG_CUERPO and ALC_MIN <= r["alcance_min"] and r["alcance"] <= ALC_MAX and r["holg_tubo"] >= HOLG_TUBO)
            mejores.append((ok, min(r["holg_cuerpo"] - HOLG_CUERPO, r["holg_tubo"] - HOLG_TUBO, ALC_MAX - r["alcance"], r["alcance_min"] - ALC_MIN), r))
    return mejores


D_VOLANTE, CORTE = 0.30, 0.04          # volante de fondo plano: Ø300 con 40 mm cortados abajo
MARGEN_VISTA = 0.09                    # el borde superior del aro queda >= 90 mm bajo los ojos
HOLG_MIN_CUERPO = 0.05


def recomendar():
    """Punto del cubo con más margen mínimo (cuerpo, alcance centrado, vista) y la columna con UNA junta cardán que pasa bajo
    los travesaños del chasis. Devuelve dict con las coordenadas."""
    CORTE_ANTES = globals()["CORTE_ARO"]
    globals()["CORTE_ARO"] = CORTE
    p = BK.postura(BK.NOMINAL["hx"], BK.NOMINAL["hy"], BK.NOMINAL["recline"])
    ojo_y = p["ojo"][1]
    mejor = None
    for x in np.arange(1.10, 1.42, 0.01):
        for y in np.arange(0.50, 0.80, 0.01):
            r = evaluar(np.array([x, y, Z_PIL]), D_VOLANTE)
            top = y + D_VOLANTE / 2 * 0.97
            marg = min(r["holg_cuerpo"] - HOLG_MIN_CUERPO, (ojo_y - MARGEN_VISTA) - top, ALC_MAX - r["alcance"], r["alcance_min"] - ALC_MIN)
            if marg > 0 and (mejor is None or marg > mejor[0]):
                mejor = (marg, np.array([x, y, Z_PIL]), r, top)
    marg, hub, r, top = mejor
    # columna: piñón -> J1 -> cubo. Mínimo ángulo de junta con la columna a >= HOLG_TUBO de todo tubo y >= 50 mm del cuerpo.
    caps = BK.capsulas(p, z=Z_PIL)

    def holg_poli(pts):
        h = 9.0
        for a, b in zip(pts[:-1], pts[1:]):
            for ta, tb, rt, nom in TUBOS:
                if min(np.linalg.norm(ta - a), np.linalg.norm(tb - a), np.linalg.norm(ta - b), np.linalg.norm(tb - b)) < 0.03:
                    continue
                aa = a + 0.04 * (b - a) / np.linalg.norm(b - a) if np.allclose(a, PINON) else a
                h = min(h, dist_seg_seg(aa, b, ta, tb) - rt - R_COL)
            for c in caps:
                if c["nombre"] in ("muslo", "pierna", "pie", "torso", "cabeza"):
                    h = min(h, dist_seg_seg(a, b, c["a"], c["b"]) - c["r"] - R_COL - 0.03)   # 30 mm extra por piel/rodilla en movimiento
        return h
    sol = None
    for xj in np.arange(0.62, 1.10, 0.01):
        for yj in np.arange(0.36, 0.66, 0.005):
            J = np.array([xj, yj, Z_PIL])
            if holg_poli([PINON, J, hub]) < HOLG_TUBO:
                continue
            u1, u2 = (J - PINON), (hub - J)
            ang = np.degrees(np.arccos(np.clip(u1 @ u2 / np.linalg.norm(u1) / np.linalg.norm(u2), -1, 1)))
            if sol is None or ang < sol[0]:
                sol = (ang, J)
    return dict(hub=hub, holg_cuerpo=r["holg_cuerpo"], alcance=r["alcance"], top=top, ojo_y=ojo_y, junta=sol,
                holg_col=holg_poli([PINON, sol[1], hub]) if sol else None, margen=marg)


if __name__ == "__main__":
    R = recomendar()
    h = R["hub"]
    print(f"VOLANTE de fondo plano Ø{D_VOLANTE*1000:.0f} mm (corte {CORTE*1000:.0f} mm): cubo en x={h[0]:.2f}, y={h[1]:.2f}, z=+-{Z_PIL:.2f}")
    print(f"  aro a {R['holg_cuerpo']*1000:.0f} mm de muslos/rodillas · alcance {R['alcance']:.2f} m · borde superior y={R['top']:.2f} ({(R['ojo_y']-R['top'])*1000:.0f} mm bajo el ojo)")
    if R["junta"]:
        ang, J = R["junta"]
        print(f"COLUMNA: piñón ({PINON[0]:.2f},{PINON[1]:.2f}) -> cardán en ({J[0]:.2f},{J[1]:.2f}) -> cubo; ángulo de la junta {ang:.1f}°; "
              f"columna a {R['holg_col']*1000:.0f} mm de tubos y cuerpo")
    else:
        print("COLUMNA: no hay trazo de una junta que libre los tubos")
