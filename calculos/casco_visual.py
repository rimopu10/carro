# -*- coding: utf-8 -*-
"""
Casco visual: reconstruye la carrocería en 3D a partir de las TRES vistas de la lámina.

Por qué existe este archivo: intentar dibujar la superficie tecleando coordenadas no
converge — sale jabón. La técnica correcta para "replicar una imagen en 3D" es el
casco visual (visual hull): la forma es la INTERSECCIÓN de las siluetas extruidas de
cada vista ortogonal. Es lo que usa la reconstrucción por fotos.

  · vista LATERAL  -> para cada estación x, hasta dónde sube y baja la carrocería
  · vista CENITAL  -> para cada estación x, cuánto ancho tiene
  · vista FRONTAL  -> para cada altura y, cuánto ancho tiene  ← la forma de la sección

La sección en la estación x es entonces, para cada altura y del rango que permite la
lateral:   semiancho(y) = min( ancho_cenital(x), ancho_frontal(y) )

Limitación honesta: el casco visual no puede capturar concavidades que no se vean en
la silueta (una toma de aire hundida, por ejemplo). Para un cuerpo de carro, que es
casi convexo, la aproximación es buena; los huecos se cortan después.

Correr:  python calculos/casco_visual.py
Salidas: ref/casco-visual.json          secciones normalizadas
         ref/casco-verificacion.png     qué silueta se usó de cada vista
"""
import json
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "ref")

# Recortes de cada vista dentro de la lámina, en fracción de la imagen.
# El cenital se corta antes del rótulo y de la foto de interior que van debajo.
CAJAS = {
    "lateral": (0.500, 0.050, 0.868, 0.318),
    "frontal": (0.048, 0.062, 0.232, 0.322),
    "cenital": (0.700, 0.322, 0.983, 0.612),
}
UMBRAL = 198
MIN_RUN = 5
N_EST = 96          # estaciones a lo largo
N_ALT = 40          # puntos por media sección


def mascara(nombre):
    """Silueta binaria del carro en esa vista.

    Recortar por fracciones no basta: las vistas vecinas de la lámina y los rótulos se
    cuelan por los bordes. La solución robusta es quedarse con el COMPONENTE CONECTADO
    MÁS GRANDE — que es el carro — y rellenarle los huecos internos (cristales claros,
    reflejos) para que la silueta quede sólida.
    """
    from scipy import ndimage
    im = Image.open(os.path.join(REF, "ref-lamina.jpg")).convert("L")
    W, H = im.size
    c = CAJAS[nombre]
    g = np.asarray(im.crop((int(c[0] * W), int(c[1] * H),
                            int(c[2] * W), int(c[3] * H))), dtype=np.int16)
    osc = g < UMBRAL
    # cierra huecos finos de la cuadrícula antes de etiquetar
    osc = ndimage.binary_closing(osc, structure=np.ones((3, 3)), iterations=2)
    lab, n = ndimage.label(osc)
    if n == 0:
        raise SystemExit(f"no se encontro el carro en la vista {nombre}")
    tam = ndimage.sum(osc, lab, range(1, n + 1))
    m = lab == (int(np.argmax(tam)) + 1)
    m = ndimage.binary_fill_holes(m)
    m = ndimage.binary_opening(m, structure=np.ones((3, 3)))
    return m


def caja_util(m):
    filas = np.flatnonzero(m.any(axis=1))
    cols = np.flatnonzero(m.any(axis=0))
    return filas[0], filas[-1], cols[0], cols[-1]


def suavizar(v, k=7):
    pad = np.pad(v, k // 2, mode="edge")
    return np.convolve(pad, np.ones(k) / k, mode="valid")


def perfil_lateral():
    """Devuelve techo(x) y piso(x) normalizados 0..1 de la altura del carro."""
    m = mascara("lateral")
    r0, r1, c0, c1 = caja_util(m)
    m = m[r0:r1 + 1, c0:c1 + 1]
    alto, ancho = m.shape
    techo = np.zeros(ancho)
    piso = np.zeros(ancho)
    for c in range(ancho):
        f = np.flatnonzero(m[:, c])
        if len(f) == 0:
            techo[c] = piso[c] = 0.0
            continue
        techo[c] = 1.0 - f[0] / (alto - 1)
        piso[c] = 1.0 - f[-1] / (alto - 1)
    xs = np.linspace(0, 1, ancho)
    return xs, suavizar(techo), suavizar(piso)


def perfil_cenital():
    """Semiancho(x) normalizado 0..1 del semiancho máximo."""
    m = mascara("cenital")
    r0, r1, c0, c1 = caja_util(m)
    m = m[r0:r1 + 1, c0:c1 + 1]
    alto, ancho = m.shape
    # la vista cenital de la lámina está con el morro arriba: el eje largo es el
    # vertical de la imagen, así que se trabaja por filas
    largo, cruz = (alto, ancho) if alto > ancho else (ancho, alto)
    trans = alto <= ancho
    mm = m.T if trans else m
    semi = np.zeros(largo)
    for r in range(largo):
        f = np.flatnonzero(mm[r, :])
        semi[r] = 0.0 if len(f) == 0 else (f[-1] - f[0]) / 2.0
    semi = suavizar(semi)
    semi = semi / max(semi.max(), 1e-9)
    xs = np.linspace(0, 1, largo)
    return xs, semi


def perfil_frontal():
    """Semiancho(y) normalizado 0..1, con y de 0 (suelo) a 1 (techo)."""
    m = mascara("frontal")
    r0, r1, c0, c1 = caja_util(m)
    m = m[r0:r1 + 1, c0:c1 + 1]
    alto, ancho = m.shape
    semi = np.zeros(alto)
    for r in range(alto):
        f = np.flatnonzero(m[r, :])
        semi[r] = 0.0 if len(f) == 0 else (f[-1] - f[0]) / 2.0
    semi = suavizar(semi)
    semi = semi / max(semi.max(), 1e-9)
    ys = np.linspace(1, 0, alto)          # fila 0 es el techo
    orden = np.argsort(ys)
    return ys[orden], semi[orden]


def main():
    xs_l, techo, piso = perfil_lateral()
    xs_c, semi_c = perfil_cenital()
    ys_f, semi_f = perfil_frontal()

    # ¿el cenital va con el morro en el mismo sentido que la lateral? Se decide por
    # dónde es más angosto: el morro de este concepto es más agudo que la cola.
    if semi_c[:len(semi_c) // 3].mean() > semi_c[-len(semi_c) // 3:].mean():
        semi_c = semi_c[::-1]

    est = []
    for xn in np.linspace(0.0, 1.0, N_EST):
        yt = float(np.interp(xn, xs_l, techo))
        yb = float(np.interp(xn, xs_l, piso))
        wc = float(np.interp(xn, xs_c, semi_c))
        if yt - yb < 0.01 or wc < 0.005:
            continue
        pts = []
        for yn in np.linspace(yb, yt, N_ALT):
            wf = float(np.interp(yn, ys_f, semi_f))
            pts.append([round(yn, 5), round(min(wc, wf), 5)])
        est.append({"x": round(float(xn), 5), "sec": pts})

    datos = {"estaciones": est,
             "n_alt": N_ALT,
             "nota": "y y z normalizados 0..1 (z sobre el semiancho maximo)"}
    with open(os.path.join(REF, "casco-visual.json"), "w", encoding="utf-8") as f:
        json.dump(datos, f, separators=(",", ":"))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 4, figsize=(20, 4.6), facecolor="#0d1117")
    for ax in axs:
        ax.set_facecolor("#0d1117")
        ax.tick_params(colors="#8b949e", labelsize=8)
        for s in ax.spines.values():
            s.set_color("#30363d")
    axs[0].plot(xs_l, techo, color="#58a6ff", lw=2, label="techo")
    axs[0].plot(xs_l, piso, color="#f0a868", lw=2, label="piso")
    axs[0].set_title("LATERAL — altura por estación", color="#c9d1d9", fontsize=10)
    axs[0].legend(fontsize=8, facecolor="#161b22", labelcolor="#c9d1d9")
    axs[1].plot(xs_c, semi_c, color="#3fb950", lw=2)
    axs[1].set_title("CENITAL — semiancho por estación", color="#c9d1d9", fontsize=10)
    axs[2].plot(semi_f, ys_f, color="#d2a8ff", lw=2)
    axs[2].set_title("FRONTAL — semiancho por altura", color="#c9d1d9", fontsize=10)
    for e in est[::6]:
        p = np.array(e["sec"])
        axs[3].plot(np.r_[-p[::-1, 1], p[:, 1]], np.r_[p[::-1, 0], p[:, 0]],
                    lw=1.1, alpha=0.85)
    axs[3].set_aspect("equal")
    axs[3].set_title("SECCIONES resultantes", color="#c9d1d9", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(REF, "casco-verificacion.png"), dpi=110, facecolor="#0d1117")

    print(f"OK  {len(est)} estaciones · {N_ALT} puntos por media sección")
    print(f"    techo max {techo.max():.3f} · semiancho cenital max {semi_c.max():.3f}")
    print(f"OK  {os.path.normpath(os.path.join(REF, 'casco-visual.json'))}")


if __name__ == "__main__":
    main()
