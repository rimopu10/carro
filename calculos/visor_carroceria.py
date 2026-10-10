# -*- coding: utf-8 -*-
"""
Genera un visor 3D interactivo de la carrocería paramétrica + el chasis.

Se arma a partir de las dos fuentes de verdad del proyecto:
  cad/superficie-param.json   las 120 secciones de la carrocería
  cad/chasis.json             los 77 tubos del chasis

Todo va embebido en el HTML: se abre con doble clic, sin servidor y sin depender de
que los archivos vecinos existan.

Correr:  python calculos/visor_carroceria.py
Salida:  carroceria-3d.html
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(HERE, "..")
CAD = os.path.join(RAIZ, "cad")

S = json.load(open(os.path.join(CAD, "superficie-param.json"), encoding="utf-8"))
CH = json.load(open(os.path.join(CAD, "chasis.json"), encoding="utf-8"))


def piel():
    """Reconstruye la rejilla de la carrocería desde las secciones y la triangula."""
    xs = S["x"]
    cy = S["centro_y"]
    R = S["radios"]
    med = len(R[0])
    pos, idx, anillos = [], [], []
    for i, x in enumerate(xs):
        fila = []
        for k in range(med):                       # lado +z, de abajo a arriba
            a = -math.pi / 2 + math.pi * k / (med - 1)
            r = R[i][k]
            fila.append(len(pos) // 3)
            pos += [x, cy[i] + r * math.sin(a), r * math.cos(a)]
        for k in range(med - 2, 0, -1):            # espejo, sin repetir polos
            a = -math.pi / 2 + math.pi * k / (med - 1)
            r = R[i][k]
            fila.append(len(pos) // 3)
            pos += [x, cy[i] + r * math.sin(a), -r * math.cos(a)]
        anillos.append(fila)
    n = len(anillos[0])
    for i in range(len(anillos) - 1):
        A, B = anillos[i], anillos[i + 1]
        for k in range(n):
            k2 = (k + 1) % n
            idx += [A[k], B[k], B[k2], A[k], B[k2], A[k2]]
    # tapas: abanico desde el centro de cada anillo extremo
    for an, inv in ((anillos[0], True), (anillos[-1], False)):
        c = len(pos) // 3
        px = sum(pos[3 * v] for v in an) / len(an)
        py = sum(pos[3 * v + 1] for v in an) / len(an)
        pz = sum(pos[3 * v + 2] for v in an) / len(an)
        pos += [px, py, pz]
        for k in range(len(an)):
            k2 = (k + 1) % len(an)
            idx += [c, an[k2], an[k]] if inv else [c, an[k], an[k2]]
    return pos, idx, anillos, med


def lineas_seccion(pos, anillos, cada=8):
    """Aristas de algunas secciones, para que se vea que la superficie es paramétrica."""
    seg = []
    for i in range(0, len(anillos), cada):
        an = anillos[i]
        for k in range(len(an)):
            a, b = an[k], an[(k + 1) % len(an)]
            seg += [pos[3 * a], pos[3 * a + 1], pos[3 * a + 2],
                    pos[3 * b], pos[3 * b + 1], pos[3 * b + 2]]
    return seg


def tubos():
    """Chasis: cada tubo como prisma orientado."""
    pos, idx = [], []
    for t in CH["tubos"]:
        A = np.array(t["a"], float)
        B = np.array(t["b"], float)
        d = B - A
        L = np.linalg.norm(d)
        if L < 1e-6:
            continue
        u = d / L
        ref = np.array([0, 1.0, 0]) if abs(u[1]) < 0.95 else np.array([1.0, 0, 0])
        e1 = np.cross(u, ref)
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(u, e1)
        s = t["sec"]
        if s["tipo"] == "redondo":
            r = s["d"] / 2
            perfil = [(r * math.cos(2 * math.pi * k / 10), r * math.sin(2 * math.pi * k / 10))
                      for k in range(10)]
        else:
            h = s["b"] / 2
            perfil = [(-h, -h), (h, -h), (h, h), (-h, h)]
        n = len(perfil)
        base = len(pos) // 3
        for P in (A, B):
            for (a1, a2) in perfil:
                q = P + e1 * a1 + e2 * a2
                pos += [float(q[0]), float(q[1]), float(q[2])]
        for k in range(n):
            k2 = (k + 1) % n
            idx += [base + k, base + k2, base + n + k2,
                    base + k, base + n + k2, base + n + k]
    return pos, idx


def ruedas():
    pos, idx = [], []
    for r in CH["ruedas"]:
        x, z, R, W = r["x"], r["z"], r["R"], r["W"]
        n = 28
        base = len(pos) // 3
        for zz in (z - W / 2, z + W / 2):
            for k in range(n):
                a = 2 * math.pi * k / n
                pos += [x + R * math.cos(a), R + R * math.sin(a), zz]
        for k in range(n):
            k2 = (k + 1) % n
            idx += [base + k, base + k2, base + n + k2,
                    base + k, base + n + k2, base + n + k]
        for off, inv in ((0, True), (n, False)):
            c = len(pos) // 3
            pos += [x, R, (z - W / 2) if off == 0 else (z + W / 2)]
            for k in range(n):
                k2 = (k + 1) % n
                idx += ([c, base + off + k2, base + off + k] if inv
                        else [c, base + off + k, base + off + k2])
    return pos, idx


def main():
    p_piel, i_piel, anillos, med = piel()
    p_tubo, i_tubo = tubos()
    p_rue, i_rue = ruedas()
    datos = {
        "piel": {"pos": [round(v, 4) for v in p_piel], "idx": i_piel,
                 "med": med, "anillos": len(anillos)},
        "secciones": [round(v, 4) for v in lineas_seccion(p_piel, anillos)],
        "chasis": {"pos": [round(v, 4) for v in p_tubo], "idx": i_tubo},
        "ruedas": {"pos": [round(v, 4) for v in p_rue], "idx": i_rue},
        "cotas": S["cotas"],
        "stats": {"cuadrangulos": (len(anillos) - 1) * (2 * med - 2),
                  "tubos": len(CH["tubos"]),
                  "masa_chasis": CH["chasis"]["masa"],
                  "ktors": CH["chasis"]["ktors"]},
    }
    # la malla DETALLADA de la IA, diezmada para que quepa en el HTML: es la que
    # conserva la toma de aire hundida y los labios de las salpicaderas
    det = os.path.join(CAD, "detallada.json")
    if os.path.exists(det):
        datos["detallada"] = json.load(open(det, encoding="utf-8"))
        print(f"    detallada: {datos['detallada']['caras']} triangulos")
    plantilla = open(os.path.join(HERE, "_visor_carroceria.html"), encoding="utf-8").read()
    salida = os.path.join(RAIZ, "carroceria-3d.html")
    html = plantilla.replace("__DATA__", json.dumps(datos, separators=(",", ":")))
    open(salida, "w", encoding="utf-8").write(html)
    print(f"OK  piel {datos['stats']['cuadrangulos']} cuadrangulos · "
          f"chasis {datos['stats']['tubos']} tubos")
    print(f"OK  {os.path.normpath(salida)}  ({len(html)//1024} KB)")


if __name__ == "__main__":
    main()
