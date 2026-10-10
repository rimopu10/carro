# -*- coding: utf-8 -*-
"""
Extrae la FIRMA DE LUZ de las imagenes de referencia y la deja en coordenadas del
carro, lista para cortarla sobre la piel en Blender.

Por que asi y no a mano: las luces no son volumen, son geometria dura, y ningun
reconstructor 3D las devuelve — se pierden en la nube de puntos. Pero SI estan en la
lamina, y estan en un color que ningun otro pixel del carro tiene: las delanteras son
lo unico azulado y brillante, las traseras lo unico rojo saturado. Se aislan por color,
se vectorizan y se llevan a fraccion del ancho / fraccion del alto del carro. Asi la
firma que sale es la de TU imagen, no una interpretacion mia.

Salida: cad/firma-luces.json
    { "frontal": [[[u,v],...], ...], "trasera": [...] }
    u = 0 en el plano de simetria, 1 en el flanco (mitad del ancho)
    v = 0 en el suelo, 1 en el techo
Solo se guarda el lado +u: el carro es simetrico y el otro lado se espeja al cortar.

Correr:  python calculos/firma_luces.py
"""
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(HERE, "..")
REF = os.path.join(RAIZ, "ref", "gemini")

# (archivo, prueba de color, area minima, nucleo de cierre, banda v permitida)
# El cierre de la trasera es HORIZONTAL y largo a proposito: la barra cruza todo el
# ancho pero el degradado del render la parte en trozos. Un nucleo cuadrado del mismo
# tamano se la tragaria contra el triangulo central, que esta 1 % mas abajo.
#
# Las zonas OSCURAS (parrilla, difusor) se cortan por debajo de v=0.55: mas arriba lo
# unico oscuro es el parabrisas, que en la lamina lateral refleja claro y por tanto no
# se puede segmentar por brillo de forma consistente en las tres vistas.
RECETAS = {
    "luz_frontal": ("ia-frontal.png",
                    lambda r, g, b, L: (b - r > 12) & (L > 130), 220, (3, 3), (0, 1)),
    "luz_trasera": ("ia-trasera.png",
                    lambda r, g, b, L: (r - b > 55) & (r > 90), 220, (1, 25), (0, 1)),
    "oscuro_frontal": ("ia-frontal.png",
                       lambda r, g, b, L: L < 58, 1500, (5, 5), (0.0, 0.55)),
    "oscuro_trasera": ("ia-trasera.png",
                       lambda r, g, b, L: L < 58, 1500, (5, 5), (0.0, 0.55)),
}


def cadena(mask):
    """Contorno exterior de una mancha, en orden, por marcha de Moore.

    Se hace a mano en vez de con una libreria de vision porque lo unico que hace
    falta es el borde exterior ordenado, y traer OpenCV por eso seria absurdo.
    """
    ys, xs = np.where(mask)
    inicio = (int(ys.min()), int(xs[ys == ys.min()].min()))
    VEC = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
    H, W = mask.shape

    def dentro(p):
        return 0 <= p[0] < H and 0 <= p[1] < W and mask[p]

    borde = [inicio]
    actual, dirn = inicio, 0
    for _ in range(200000):
        for k in range(8):
            d = (dirn + 6 + k) % 8            # retroceder y barrer en sentido horario
            v = VEC[d]
            sig = (actual[0] + v[0], actual[1] + v[1])
            if dentro(sig):
                actual, dirn = sig, d
                break
        else:
            break
        if actual == inicio and len(borde) > 3:
            break
        borde.append(actual)
    return borde


def simplificar(pts, tol):
    """Douglas-Peucker. Deja los quiebres (que en una firma de luz son todo) y tira
    los cientos de puntos de escalera que aporta el rasterizado."""
    if len(pts) < 3:
        return pts
    a, b = np.array(pts[0], float), np.array(pts[-1], float)
    ab = b - a
    n = np.linalg.norm(ab)
    P = np.array(pts, float)
    # cruz 2D a mano: numpy 2 quito np.cross para vectores de dos componentes
    d = (np.abs(ab[0] * (P[:, 1] - a[1]) - ab[1] * (P[:, 0] - a[0])) / n if n > 1e-9
         else np.linalg.norm(P - a, axis=1))
    i = int(d.argmax())
    if d[i] <= tol:
        return [pts[0], pts[-1]]
    return simplificar(pts[:i + 1], tol)[:-1] + simplificar(pts[i:], tol)


def extraer(nombre):
    arch, prueba, area_min, nucleo, (vlo, vhi) = RECETAS[nombre]
    im = Image.open(os.path.join(REF, arch)).convert("RGBA")
    a = np.asarray(im).astype(int)
    alfa = a[:, :, 3] > 128
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    luz = alfa & prueba(r, g, b, (r + g + b) / 3.0)

    ys, xs = np.where(alfa)
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    semi = (x1 - x0) / 2.0
    cx = (x0 + x1) / 2.0
    alto = float(y1 - y0)

    v = (y1 - np.arange(a.shape[0])) / alto
    luz &= ((v >= vlo) & (v < vhi))[:, None]

    # SIMETRIZAR sobre el eje del carro antes de vectorizar. El render de referencia
    # tiene el punto de fuga ligeramente corrido y una luz sale 20 px mas larga que la
    # otra; un carro que se va a fabricar no puede heredar ese error.
    franja = luz[:, x0:x1 + 1]
    luz[:, x0:x1 + 1] = franja | np.fliplr(franja)
    luz = ndimage.binary_closing(luz, np.ones(nucleo))

    etiq, n = ndimage.label(luz)
    elegidas = []
    for i in range(1, n + 1):
        m = etiq == i
        if m.sum() < area_min:
            continue
        pol = [((px - cx) / semi, (y1 - py) / alto)
               for (py, px) in simplificar(cadena(m), 1.6)]
        elegidas.append((m.sum(), pol))

    elegidas.sort(key=lambda t: (-min(p[1] for p in t[1]), t[1][0][0]))
    for k, (area, pol) in enumerate(elegidas, 1):
        print(f"    {nombre:8s} pieza {k}: {area:6d} px  {len(pol):3d} vertices  "
              f"u[{min(p[0] for p in pol):+.2f},{max(p[0] for p in pol):+.2f}]  "
              f"v[{min(p[1] for p in pol):.2f},{max(p[1] for p in pol):.2f}]")
    return [p for _, p in elegidas]


def main():
    datos = {n: extraer(n) for n in RECETAS}
    dest = os.path.join(RAIZ, "cad", "firma-luces.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump({k: [[[round(u, 4), round(v, 4)] for u, v in pol] for pol in ps]
                   for k, ps in datos.items()}, f, separators=(",", ":"))
    print("OK  " + os.path.normpath(dest))


if __name__ == "__main__":
    main()
