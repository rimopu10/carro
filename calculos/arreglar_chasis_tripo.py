# -*- coding: utf-8 -*-
"""
Barrido de los nodos del chasis que chocan con la piel de Tripo (ver verificar_piel_tripo.py):
mueve dash_hi (pie del pilar A) y hdr (esquina de cabecera) lo MÍNIMO para dejar >= AIRE_MIN
de aire hasta la piel exterior (ya descontado el cascarón de 12 mm), re-corre el FEM entero
y reporta K_torsional y los FS de cada caso. La carrocería no se toca.

    python calculos/arreglar_chasis_tripo.py <stl_cerrado_sin_ruedas>
"""
import contextlib, io, itertools, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from verificar_piel_tripo import aire_tubo, cargar_piel, SANDWICH  # noqa: E402

AIRE_MIN = 0.004      # m de aire sobre el cascarón (4 mm) — sólo para no tocar piel
SRC = open(os.path.join(HERE, "analisis_chasis.py"), encoding="utf-8").read()


def fem(dash=None, hdr=None):
    s = SRC
    if dash:
        s = s.replace('NM("dash_hi", 0.95, 0.72, 0.48)', 'NM("dash_hi", %r, %r, %r)' % dash)
    if hdr:
        s = s.replace('NM("hdr",   1.45, 0.95, 0.42)', 'NM("hdr",   %r, %r, %r)' % hdr)
    ns = {"__name__": "x", "__file__": os.path.join(HERE, "analisis_chasis.py")}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(s, "analisis", "exec"), ns)
    return ns, buf.getvalue()


def aires(pg, ns, nodos):
    peor = (np.inf, "")
    for a, b, sec, tag in ns["MEMBERS"]:
        if not any(n in (a, b) for n in nodos):
            continue
        m, p, d = aire_tubo(pg, ns["NODES"][a], ns["NODES"][b], sec["c"], n=7)
        if m - SANDWICH < peor[0]:
            peor = (m - SANDWICH, f"{a}-{b} {d}")
    return peor


if __name__ == "__main__":
    pg = cargar_piel(sys.argv[1])
    ns, out = fem()
    print("BASE:\n" + out)
    nod = ["dash_hiL", "dash_hiR", "hdrL", "hdrR"]
    print("base aire:", aires(pg, ns, nod))
    res = []
    for y, z in itertools.product((0.72, 0.70, 0.68, 0.66, 0.64), (0.48, 0.45, 0.42, 0.40)):
        ns, out = fem(dash=(0.95, y, z))
        a = aires(pg, ns, ["dash_hiL", "dash_hiR"])
        k = re.search(r"K_torsional ([\d,]+)", out).group(1)
        fs = re.findall(r"FS_min = ([\d.]+)", out)
        res.append((y, z, a[0], a[1], k, fs))
        print(f"dash_hi y={y:.2f} z={z:.2f}  aire {a[0]*1000:+6.1f} mm ({a[1]})  K={k}  FS {fs}", flush=True)
