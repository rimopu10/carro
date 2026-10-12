# -*- coding: utf-8 -*-
"""
¿El carro raspa en un tope? Simulación 2D rígida (sin compresión de suspensión: peor caso a
baja velocidad) del perfil inferior de la piel de Tripo + tubos del chasis pasando de frente
sobre un tope en arco. Reporta, por altura de tope, cuánto se mete cada zona (negativo).

    python calculos/topes.py
"""
import json, os
import numpy as np, trimesh

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
Z_CENTRO = 0.62          # |z| de la carrocería propiamente (fuera de esto están los pozos y llantas)


def perfil_inferior():
    ch = json.load(open(os.path.join(RAIZ, "cad", "chasis.json"), encoding="utf-8"))
    m = trimesh.load(os.path.join(RAIZ, "cad", "carroceria-tripo-solida-mm.stl")); m.apply_scale(0.001)
    V = m.vertices[np.abs(m.vertices[:, 2]) < Z_CENTRO]
    xs = np.arange(-0.32, 3.64, 0.02)
    prof = {}
    for x in xs:
        s = V[np.abs(V[:, 0] - x) < 0.02]
        if len(s): prof[round(x, 2)] = s[:, 1].min()
    # tubos del chasis: borde inferior
    tub = {}
    for t in ch["tubos"]:
        r = (t["sec"].get("d") or t["sec"].get("b")) / 2
        for u in np.linspace(0, 1, 40):
            p = np.array(t["a"]) + (np.array(t["b"]) - np.array(t["a"])) * u
            k = round(round(p[0] / 0.02) * 0.02, 2)
            tub[k] = min(tub.get(k, 9), p[1] - r)
    return ch, prof, tub


def tope(h, w):
    Rc = (h * h + (w / 2) ** 2) / (2 * h)
    return lambda x: np.where(np.abs(x) < w / 2, np.sqrt(np.maximum(Rc ** 2 - x ** 2, 0)) - (Rc - h), 0.0)


def centro_rueda(g, xc, R):
    xx = np.linspace(xc - R, xc + R, 120)
    return float(np.max(g(xx) + np.sqrt(np.maximum(R ** 2 - (xc - xx) ** 2, 0))))


def correr(prof, ch, h, w, label):
    Rf, Rr = ch["ruedas"][0]["R"], ch["ruedas"][2]["R"]
    xa, xb = ch["ruedas"][0]["x"], ch["ruedas"][2]["x"]
    th0 = np.arctan2(Rr - Rf, xb - xa)
    X = np.array(list(prof)); Y = np.array([prof[k] for k in prof])
    g = tope(h, w)
    peor = {}
    for xf in np.arange(-1.6, 5.0, 0.02):
        yf = centro_rueda(g, xf, Rf); yr = centro_rueda(g, xf + xb - xa, Rr)
        th = np.arctan2(yr - yf, xb - xa); d = th - th0
        dx, dy = X - xa, Y - Rf
        wx = xf + dx * np.cos(d) - dy * np.sin(d)
        wy = yf + dx * np.sin(d) + dy * np.cos(d)
        cl = wy - g(wx)
        i = int(np.argmin(cl))
        zona = "nariz" if X[i] < 0.3 else ("cola" if X[i] > 2.9 else "vientre")
        if zona not in peor or cl[i] < peor[zona][0]: peor[zona] = (cl[i], X[i])
    print(f"  {label:34s}" + "  ".join(f"{z}: {v[0]*1000:+5.0f} mm (x={v[1]:.2f})" for z, v in sorted(peor.items())))


if __name__ == "__main__":
    ch, prof, tub = perfil_inferior()
    print("perfil inferior (piel):", {k: round(v * 1000) for k, v in list(prof.items())[::15]})
    print("tubos más bajos x:", {k: round(v * 1000) for k, v in sorted(tub.items(), key=lambda a: a[1])[:3]})
    for h in (0.06, 0.08, 0.10, 0.12, 0.15):
        for w in (0.8, 1.5):
            correr(prof, ch, h, w, f"tope {h*100:.0f} cm × {w:.1f} m")
