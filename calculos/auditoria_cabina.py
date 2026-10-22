# -*- coding: utf-8 -*-
"""
AUDITORÍA DE CABINA: ¿qué tubos del chasis (cad/chasis.json) estorban al cuerpo o a la vista de los ocupantes?

  A. CUERPO: distancia de cada tubo a las cápsulas del cuerpo (buck_piloto.capsulas) del piloto (z=+0.31) y del pasajero
     (z=-0.31), en 5 posiciones del asiento sobre el riel y para 3 estaturas. Negativa = el tubo atraviesa el cuerpo.
  B. ASIENTO: tubos dentro de la huella del asiento (cojín + respaldo + riel) por encima de su plano de apoyo.
  C. VISTA: desde los ojos (65 mm entre pupilas) cuánto ángulo tapa cada tubo hacia adelante: obscuración binocular
     (la que no ve NINGÚN ojo) y monocular, a la altura de los ojos, y límite superior de la vista (semáforos).
  D. Cosas parecidas: cabeza vs riel del techo, hombro vs patas del arco, rodillas/espinillas vs travesaños del tablero,
     pies vs tubos de la nariz, espalda vs barra de cinturones.

    python calculos/auditoria_cabina.py
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

CH = json.load(open(os.path.join(HERE, "..", "cad", "chasis.json"), encoding="utf-8"))
TUBOS = [dict(nom=t["nom"], a=np.array(t["a"], float), b=np.array(t["b"], float),
              r=(t["sec"].get("d") or t["sec"].get("b")) / 2) for t in CH["tubos"]]
SEP_OJOS = 0.065


def dist_seg_seg(p1, q1, p2, q2):
    u, v, w = q1 - p1, q2 - p2, p1 - p2
    a, b, c, d, e = u @ u, u @ v, v @ v, u @ w, v @ w
    D = a * c - b * b
    s = 0.0 if D < 1e-14 else (b * e - c * d) / D
    s = float(np.clip(s, 0, 1))
    t = (b * s + e) / c if c > 1e-14 else 0.0
    t = float(np.clip(t, 0, 1))
    s = float(np.clip((b * t - d) / a, 0, 1)) if a > 1e-14 else 0.0
    return float(np.linalg.norm((p1 + s * u) - (p2 + t * v)))


def posiciones():
    """(etiqueta, estatura, hx) -- asiento a lo largo del riel y las tres estaturas de diseño."""
    pos = [(f"1.75 m riel x={hx:.2f}", 1.75, hx) for hx in np.linspace(BK.RIELES[0], BK.RIELES[1], 5)]
    pos += [("1.60 m adelante", 1.60, BK.RIELES[0]), (f"{BK.ESTATURA_MAX:.2f} m atrás", BK.ESTATURA_MAX, BK.RIELES[1])]
    return pos


def cuerpo(imprimir=True):
    if imprimir:
        print("=" * 100)
        print("A. TUBOS vs CUERPO  (holgura = distancia al eje de la cápsula - radio del cuerpo - radio del tubo; <0 = atraviesa)")
    peor = {}
    for lado, z in (("piloto", 0.31), ("pasajero", -0.31)):
        for etq, est, hx in posiciones():
            p = BK.postura(hx, BK.NOMINAL["hy"], BK.NOMINAL["recline"], estatura=est)
            for c in BK.capsulas(p, z=z):
                for t in TUBOS:
                    h = dist_seg_seg(c["a"], c["b"], t["a"], t["b"]) - c["r"] - t["r"]
                    k = (lado, t["nom"], c["nombre"])
                    if k not in peor or h < peor[k][0]:
                        peor[k] = (h, etq)
    malos = sorted((v[0], k, v[1]) for k, v in peor.items() if v[0] < 0.03)
    if not imprimir:
        return malos
    if not malos:
        print("  NINGÚN tubo a menos de 30 mm del cuerpo.")
    for h, (lado, nom, parte), etq in malos[:40]:
        marca = "ATRAVIESA" if h < 0 else "justo   "
        print(f"  {marca} {lado:9s} {parte:7s} {nom:16s} holgura {h*1000:+5.0f} mm   ({etq})")
    return malos


def asiento():
    """Huella del asiento: cojín + cubeta + respaldo. Un tubo que asoma sobre el plano de apoyo dentro de la huella
    (o que cruza el respaldo) pasa 'por donde están los asientos'."""
    print("=" * 100)
    print("B. TUBOS DENTRO DE LA HUELLA DEL ASIENTO (cojín, cubeta, respaldo y recorrido del riel)")
    hits = []
    hx0, hx1 = BK.RIELES
    hy, th = BK.NOMINAL["hy"], np.radians(BK.NOMINAL["recline"])
    for lado, zc in (("piloto", 0.31), ("pasajero", -0.31)):
        # cojín: x de la rodilla (hx-0.43) a la cadera (+0.10), y desde 0.20 (apoyo sobre travesaño+riel) hasta la cadera
        # respaldo: del plano de la cadera al hombro (inclinado 40 grados), grosor de cubeta 0.04, ancho 0.46
        pan = dict(x=(hx0 - 0.42, hx1 + 0.10), y=(0.195, hy + 0.04), z=(zc - 0.23, zc + 0.23))
        for t in TUBOS:
            P = t["a"] + (t["b"] - t["a"]) * np.linspace(0, 1, 400)[:, None]
            dentro = ((P[:, 0] > pan["x"][0]) & (P[:, 0] < pan["x"][1]) & (P[:, 2] > pan["z"][0]) & (P[:, 2] < pan["z"][1])
                      & (P[:, 1] + t["r"] > pan["y"][0]) & (P[:, 1] - t["r"] < pan["y"][1]))
            if dentro.any():
                L = dentro.mean() * np.linalg.norm(t["b"] - t["a"])
                hits.append((lado, t["nom"], L, P[dentro].mean(axis=0), P[dentro][:, 1].max() + t["r"]))
        # respaldo: plano inclinado desde la cadera (hx, hy) hacia (hx+0.51 sen, hy+0.51 cos); tubos a menos de 0.10 del plano
        for hx in (hx0, (hx0 + hx1) / 2, hx1):
            hip = np.array([hx, hy]); dirr = np.array([np.sin(th), np.cos(th)])
            for t in TUBOS:
                n = 0
                for s in np.linspace(0, 1, 400):
                    q = t["a"] + (t["b"] - t["a"]) * s
                    if abs(q[2] - zc) < 0.23:
                        rel = q[[0, 1]] - hip
                        along = rel @ dirr
                        perp = rel @ np.array([dirr[1], -dirr[0]])        # + = hacia atrás del respaldo
                        if 0.0 < along < 0.55 and -0.16 - t["r"] < perp < 0.04:
                            n += 1
                if n:
                    hits.append((lado + f" respaldo(x{hx:.2f})", t["nom"], n / 400 * np.linalg.norm(t["b"] - t["a"]), None, None))
    if not hits:
        print("  Ningún tubo invade la huella del asiento.")
    for lado, nom, L, c, ytop in sorted(hits, key=lambda h: -h[2]):
        ctr = f"centro ({c[0]:.2f}, {c[1]:.2f}, {c[2]:+.2f}) y_sup {ytop:.3f}" if c is not None else ""
        print(f"  {lado:26s} {nom:16s} {L*1000:6.0f} mm dentro  {ctr}")
    return hits


def ojos(p, z):
    """Ojo izquierdo y derecho (separados 65 mm en z)."""
    return [np.array([p["ojo"][0], p["ojo"][1], z + s * SEP_OJOS / 2]) for s in (+1, -1)]


def sombra(ojo, t, y_rel, ancho_y=0.012):
    """Intervalo de azimut (grados; 0 = recto adelante, + = izquierda +z) que tapa el tubo t en el plano horizontal a
    y = ojo_y + y_rel. None si el tubo no cruza esa altura."""
    ya = t["a"][1] - ojo[1]
    yb = t["b"][1] - ojo[1]
    lo, hi = min(ya, yb) - t["r"], max(ya, yb) + t["r"]
    if not (lo - 1e-9 <= y_rel <= hi + 1e-9):
        return None
    # puntos del eje del tubo a esa altura (si es horizontal, todo el tubo)
    if abs(yb - ya) < 1e-6:
        s = np.linspace(0, 1, 200)
    else:
        s0 = np.clip((y_rel - ya) / (yb - ya), 0, 1)
        s = np.array([s0])
    P = t["a"] + (t["b"] - t["a"]) * s[:, None]
    rel = P - ojo
    fwd = -rel[:, 0]                                  # x crece hacia atrás: adelante es -x
    ok = fwd > 0.05
    if not ok.any():
        return None
    az = np.degrees(np.arctan2(rel[ok, 2], fwd[ok]))
    dist = np.hypot(rel[ok, 2], fwd[ok])
    semi = np.degrees(np.arcsin(np.clip(t["r"] / dist, 0, 1)))
    return float((az - semi).min()), float((az + semi).max())


def vista():
    print("=" * 100)
    print("C. VISTA hacia adelante (azimut: 0 = recto, + = izquierda). Tubos que tapan algo en el campo ±60° a la altura de los ojos y +5, +10°")
    res = []
    for lado, z in (("piloto", 0.31), ("pasajero", -0.31)):
        for etq, est, hx in (("1.75 m", 1.75, BK.NOMINAL["hx"]), ("1.60 m", 1.60, BK.RIELES[0]), (f"{BK.ESTATURA_MAX:.2f} m", BK.ESTATURA_MAX, BK.RIELES[1])):
            p = BK.postura(hx, BK.NOMINAL["hy"], BK.NOMINAL["recline"], estatura=est)
            oL, oR = ojos(p, z)
            for dy_deg, dy in (("ojos", 0.0), ("+0.15 m", 0.15)):
                for t in TUBOS:
                    sL, sR = sombra(oL, t, dy), sombra(oR, t, dy)
                    if sL is None or sR is None:
                        continue
                    if not (-60 < (sL[0] + sL[1]) / 2 < 60):
                        continue
                    bino = max(0.0, min(sL[1], sR[1]) - max(sL[0], sR[0]))
                    mono = max(sL[1], sR[1]) - min(sL[0], sR[0])
                    res.append((lado, etq, dy_deg, t["nom"], bino, mono, (sL[0] + sL[1]) / 2))
    # la tabla útil: por lado y estatura nominal, a la altura de los ojos
    visto = set()
    for r in sorted(res, key=lambda r: -r[5]):
        if r[1] != "1.75 m" or r[2] != "ojos":
            continue
        print(f"  {r[0]:9s} ojos: {r[3]:16s} azimut {r[6]:+6.1f}°  tapa {r[5]:5.1f}° (monocular)  {r[4]:5.1f}° (binocular)")
        visto.add(r[3])
    print("  (el límite de la norma para un pilar A es 6° binocular; aquí sólo cuentan los tubos, falta sumar el pilar de la piel)")
    return res


def limite_superior():
    print("-" * 100)
    print("   Límite superior de la vista (borde de la cabecera visto desde el ojo, recto adelante)")
    for lado, z in (("piloto", 0.31), ("pasajero", -0.31)):
        for etq, est, hx in (("1.60 m", 1.60, BK.RIELES[0]), ("1.75 m", 1.75, BK.NOMINAL["hx"]), (f"{BK.ESTATURA_MAX:.2f} m", BK.ESTATURA_MAX, BK.RIELES[1])):
            p = BK.postura(hx, BK.NOMINAL["hy"], BK.NOMINAL["recline"], estatura=est)
            m = BK.metricas(p)
            print(f"   {lado:9s} {etq}: cabecera a {m['cabecera_grados']:+.1f}° sobre los ojos  "
                  f"(un semáforo a 10 m y 3.5 m de altura está a ~{np.degrees(np.arctan((3.5 - (p['ojo'][1] + 0.0)) / 10)):.0f}° sobre el ojo)")
        break


def parecidas():
    print("=" * 100)
    print("D. DETALLES PARECIDOS (holguras en mm)")
    p = BK.postura(BK.NOMINAL["hx"], BK.NOMINAL["hy"], BK.NOMINAL["recline"])
    m = BK.metricas(p)
    print(f"  techo sobre la coronilla {m['holgura_techo']*1000:+.0f} mm · nuca-arco {m['nuca_arco']*1000:+.0f} mm · "
          f"espalda-barra {m['espalda_barra']*1000:+.0f} mm · pedal x {m['pedal_x']:.2f}")
    for hx, etq in ((BK.RIELES[0], "riel adelante"), (BK.RIELES[1], "riel atrás")):
        q = BK.postura(hx, BK.NOMINAL["hy"], BK.NOMINAL["recline"])
        mm = BK.metricas(q)
        print(f"  {etq}: techo {mm['holgura_techo']*1000:+.0f} mm · nuca-arco {mm['nuca_arco']*1000:+.0f} mm · espalda-barra {mm['espalda_barra']*1000:+.0f} mm")
    # tubos más cercanos a cada parte del cuerpo (piloto, posición nominal)
    print("  Tubo más cercano a cada parte (piloto, nominal y en los dos extremos del riel):")
    for parte in ("cabeza", "torso", "muslo", "pierna", "pie"):
        mejor = []
        for hx in (BK.RIELES[0], BK.NOMINAL["hx"], BK.RIELES[1]):
            q = BK.postura(hx, BK.NOMINAL["hy"], BK.NOMINAL["recline"])
            c = next(c for c in BK.capsulas(q, z=0.31) if c["nombre"] == parte)
            mejor += [(dist_seg_seg(c["a"], c["b"], t["a"], t["b"]) - c["r"] - t["r"], t["nom"], hx) for t in TUBOS]
        mejor.sort()
        print(f"    {parte:7s}: " + " · ".join(f"{n} {h*1000:+.0f}" for h, n, hx in mejor[:3]))


def imagenes(malos):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    salida = os.path.join(HERE, "..", "docs", "auditoria-cabina")
    os.makedirs(salida, exist_ok=True)
    marcados = {k[1] for h, k, e in malos if h < 0}
    justos = {k[1] for h, k, e in malos if 0 <= h < 0.03} - marcados
    fig, axs = plt.subplots(2, 1, figsize=(15, 9))
    for ax, (ix, iy, tit) in zip(axs, ((0, 2, "Vista superior (x atrás →, z)"), (0, 1, "Vista lateral (x atrás →, y arriba)"))):
        for t in TUBOS:
            col = "#e11d48" if t["nom"] in marcados else ("#f59e0b" if t["nom"] in justos else "#94a3b8")
            lw = 3.0 if col != "#94a3b8" else 1.2
            ax.plot([t["a"][ix], t["b"][ix]], [t["a"][iy], t["b"][iy]], color=col, lw=lw, solid_capstyle="round")
        for z in (0.31, -0.31):
            for hx, al in ((BK.RIELES[0], 0.25), (BK.NOMINAL["hx"], 0.5), (BK.RIELES[1], 0.25)):
                p = BK.postura(hx, BK.NOMINAL["hy"], BK.NOMINAL["recline"])
                for c in BK.capsulas(p, z=z):
                    ax.plot([c["a"][ix], c["b"][ix]], [c["a"][iy], c["b"][iy]], color="#2563eb", alpha=al, lw=c["r"] * 230,
                            solid_capstyle="round")
        ax.set_aspect("equal"); ax.set_title(tit); ax.grid(alpha=0.3)
    axs[0].invert_yaxis() if False else None
    fig.suptitle("Chasis vs ocupantes. Rojo = atraviesa el cuerpo · Ámbar = a <30 mm · Azul = cuerpo (3 posiciones del riel)")
    fig.tight_layout()
    ruta = os.path.join(salida, "cabina-tubos-vs-cuerpo.png")
    fig.savefig(ruta, dpi=110)
    print("  imagen:", os.path.relpath(ruta))


if __name__ == "__main__":
    malos = cuerpo()
    asiento()
    vista()
    limite_superior()
    parecidas()
    imagenes(malos)
