# -*- coding: utf-8 -*-
"""
FEM del chasis REUTILIZABLE: evalúa cualquier topología (lista de miembros) y secciones.

Toma la geometría, las masas, los apoyos, las secciones y las funciones de viga de
analisis_chasis.py (se ejecuta con __file__ falso para no reescribir resultados-analisis.md ni
la lista de corte), y expone `evaluar(miembros)` con los MISMOS casos de carga:
LC1 bache 3g, LC3 frenada 1g, LC4 curva 1g, LC5 volcadura 2.0W+0.75W, LC2 torsión 1500 N·m.

    python calculos/fem_chasis.py      # paridad con analisis_chasis.py
"""
import os as _os
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    _os.environ.setdefault(_v, "1")   # sistemas chicos: con muchos hilos BLAS tarda 60x más
import contextlib
import io
import os
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "analisis_chasis.py"), encoding="utf-8").read()
_ns = {"__name__": "base", "__file__": os.path.join(tempfile.gettempdir(), "fakeproj", "calculos", "a.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(_src, "analisis_chasis", "exec"), _ns)

NODES = _ns["NODES"]
MEMBERS0 = list(_ns["MEMBERS"])            # (a, b, sec, tag) del diseño vigente
NAMES = sorted(NODES)
IDX = {n: i for i, n in enumerate(NAMES)}
NDOF = 6 * len(NAMES)


def registrar_nodo(nombre, xyz):
    """Agrega un nodo nuevo (p. ej. el centro del piso) y reindexa."""
    global NAMES, IDX, NDOF
    NODES[nombre] = np.array(xyz, float)
    NAMES = sorted(NODES)
    IDX = {n: i for i, n in enumerate(NAMES)}
    NDOF = 6 * len(NAMES)
E, FY, RHO, G = _ns["E"], _ns["FY"], _ns["RHO"], _ns["G"]
g = 9.81
MASA_TOTAL = _ns["MASA_TOTAL_CARRO"]
MASA_SUSP = _ns["MASA_SUSPENDIDA"]
_MASAS_FIJAS = {k: v for k, v in {
    "bat_fL": 22.5, "bat_fR": 22.5, "bat_rL": 22.5, "bat_rR": 22.5, "seatL": 90.0, "seatR": 90.0,
    "noseL": 7.5, "noseR": 7.5, "dash_loL": 10, "dash_loR": 10, "mh_loL": 10, "mh_loR": 10}.items()}
beam_k_local, transform, esfuerzo_max = _ns["beam_k_local"], _ns["transform"], _ns["esfuerzo_max"]
sec_ptr, sec_red = _ns["sec_ptr"], _ns["sec_red"]


def mover_masa(origen, destino):
    """destino: nodo (todo) o dict nodo->fracción. El ocupante pesa donde se atornillan sus rieles."""
    m = _MASAS_FIJAS.pop(origen)
    for n, f in (destino.items() if isinstance(destino, dict) else [(destino, 1.0)]):
        _MASAS_FIJAS[n] = _MASAS_FIJAS.get(n, 0.0) + m * f


def fix(n, comps):
    return [6 * IDX[n] + c for c in comps]


def _sup():
    return (fix("fx_hiL", [1]) + fix("fx_hiR", [1]) + fix("coilL", [1]) + fix("coilR", [1])
            + fix("fb_loL", [0, 2]) + fix("fb_loR", [2]) + fix("taL", [2]))


def _sup_t():
    return fix("coilL", [0, 1, 2]) + fix("coilR", [0, 1, 2]) + fix("taL", [0, 1, 2]) + fix("taR", [0, 1, 2])


def _masas(miembros):
    """Masa por nodo: las fijas + el faltante repartido por tubo que llega a cada nodo
    (igual que analisis_chasis.py)."""
    m = dict(_MASAS_FIJAS)
    falta = MASA_SUSP - sum(m.values())
    tubo = {n: 0.0 for n in NODES}
    for a, b, s, tag in miembros:
        L = float(np.linalg.norm(NODES[b] - NODES[a]))
        tubo[a] += L / 2
        tubo[b] += L / 2
    tot = sum(tubo.values())
    for n, L in tubo.items():
        m[n] = m.get(n, 0.0) + falta * L / tot
    return m


def _F(masas, ax=0.0, ay=-1.0, az=0.0):
    F = np.zeros(NDOF)
    for n, mm in masas.items():
        i = 6 * IDX[n]
        F[i] += mm * g * ax
        F[i + 1] += mm * g * ay
        F[i + 2] += mm * g * az
    return F


def _F_vuelco(nv, nl):
    W = MASA_TOTAL * g
    F = np.zeros(NDOF)
    for n in ("mh_hiL", "mh_hiR"):
        i = 6 * IDX[n]
        F[i + 1] -= nv * W / 2
        F[i + 2] += nl * W / 2
    return F


import puertas as _PU


def _F_puerta():
    """LC7: puertas abiertas a 65 grados. Reacciones de las bisagras y del amortiguador en los nodos h1/h2/sa."""
    F = np.zeros(NDOF)
    for n, f in _PU.lc7().items():
        if n in IDX:
            F[6 * IDX[n]:6 * IDX[n] + 6] += f
    return F


ARNES_N = 0.6 * 90.0 * 9.81 * 10.0      # 5.3 kN por asiento: 60% de 90 kg a 10 g, en la barra de cinturones


def _F_arnes(masas):
    """LC8: choque frontal a 10 g. El arnés tira de la barra de cinturones hacia adelante (-x) con ARNES_N en cada asiento
    (nodos baL/baR, z=+-0.31); el chasis se equilibra por inercia, repartida en proporción a la masa de cada nodo."""
    F = np.zeros(NDOF)
    tot = 0.0
    for n in ("baL", "baR"):
        if n in IDX:
            F[6 * IDX[n]] -= ARNES_N
            tot -= ARNES_N
    if tot == 0.0:
        return F
    M = sum(masas.values())
    for n, m in masas.items():
        F[6 * IDX[n]] -= tot * m / M
    return F


def _F_vuelco_frontal(nv, nl):
    """LC5c: la volcadura también carga la CABECERA del parabrisas (esquinas hdr), no sólo el arco."""
    W = MASA_TOTAL * g
    F = np.zeros(NDOF)
    for n in ("hdrL", "hdrR"):
        i = 6 * IDX[n]
        F[i + 1] -= nv * W / 2
        F[i + 2] += nl * W / 2
    return F


def _resolver(K, F, fixed):
    libre = np.setdiff1d(np.arange(NDOF), fixed)
    # los nodos que quedan sin miembros dejan filas nulas: regularizar
    Kl = K[np.ix_(libre, libre)] + 1e-6 * np.eye(len(libre))
    U = np.zeros(NDOF)
    U[libre] = np.linalg.solve(Kl, F[libre])
    return U


_CACHE = {}


def _elem(a, b, s):
    k = (a, b, s["nombre"])
    e = _CACHE.get(k)
    if e is None:
        T, Le = transform(NODES[a], NODES[b])
        kl = beam_k_local(Le, s)
        e = dict(a=a, b=b, sec=s, T=T, kl=kl, kg=T.T @ kl @ T, L=Le)
        _CACHE[k] = e
    return e


def ensamblar(miembros):
    K = np.zeros((NDOF, NDOF))
    elems = []
    for a, b, s, tag in miembros:
        e = dict(_elem(a, b, s), tag=tag)
        e["dof"] = np.r_[6 * IDX[a]:6 * IDX[a] + 6, 6 * IDX[b]:6 * IDX[b] + 6]
        K[np.ix_(e["dof"], e["dof"])] += e["kg"]
        elems.append(e)
    return K, elems


def _resolver_multi(K, Fm, fixed):
    libre = np.setdiff1d(np.arange(NDOF), fixed)
    Kl = K[np.ix_(libre, libre)] + 1e-6 * np.eye(len(libre))
    U = np.zeros((NDOF, Fm.shape[1]))
    U[libre] = np.linalg.solve(Kl, Fm[libre])
    return U


def evaluar(miembros):
    """-> dict(masa, K_tors, fs={caso: FS mín}, fs_miembro={(a,b): FS mín en LC1/3/4}, fs5={(a,b): FS LC5},
    pandeo={(a,b): FS Euler mín LC1/3/4}, pandeo5={(a,b): FS Euler LC5}, peor={caso: nombre})"""
    K, elems = ensamblar(miembros)
    masas = _masas(miembros)
    nombres = ["LC1", "LC3", "LC4", "LC5", "LC5c", "LC7", "LC8"]
    Fm = np.column_stack([_F(masas, 0, -3.0, 0), _F(masas, -1.0, -1.0, 0), _F(masas, 0, -1.0, 1.0),
                          _F_vuelco(2.0, 0.75), _F_vuelco_frontal(1.0, 0.5), _F_puerta(), _F_arnes(masas)])
    Um = _resolver_multi(K, Fm, _sup())
    out = dict(masa=sum(e["L"] * e["sec"]["A"] * RHO for e in elems), fs={}, peor={},
               fs_miembro={}, fs5={}, pandeo={}, pandeo5={})
    for j, caso in enumerate(nombres):
        U = Um[:, j]
        mn, nom_mn = np.inf, ""
        for e in elems:
            sig, fsb = esfuerzo_max(e, U)
            fs = FY / sig if sig > 0 else np.inf
            nom = (e["a"], e["b"])
            if caso in ("LC5", "LC5c"):
                out["fs5"][nom] = min(out["fs5"].get(nom, np.inf), fs)
            else:
                out["fs_miembro"][nom] = min(out["fs_miembro"].get(nom, np.inf), fs)
            d = out["pandeo5"] if caso in ("LC5", "LC5c") else out["pandeo"]
            d[nom] = min(d.get(nom, np.inf), fsb)
            if fs < mn:
                mn, nom_mn = fs, f"{e['a']}-{e['b']}"
        out["fs"][caso], out["peor"][caso] = mn, nom_mn
    brazo = abs(NODES["fx_hiL"][2])
    Fq = np.zeros((NDOF, 1))
    Fq[6 * IDX["fx_hiL"] + 1, 0] = 1500.0 / (2 * brazo)
    Fq[6 * IDX["fx_hiR"] + 1, 0] = -1500.0 / (2 * brazo)
    Ut = _resolver_multi(K, Fq, _sup_t())[:, 0]
    fs6 = np.inf
    for e in elems:           # bache en UNA rueda a 3g ~ 3x el par de 1500 N·m de la prueba de rigidez
        sig, _ = esfuerzo_max(e, 3.0 * Ut)
        fs6 = min(fs6, FY / sig if sig > 0 else np.inf)
    out["fs"]["LC6"] = fs6
    th = (Ut[6 * IDX["fx_hiL"] + 1] - Ut[6 * IDX["fx_hiR"] + 1]) / (2 * brazo)
    out["K_tors"] = 1500.0 / np.degrees(th) if th > 0 else 0.0
    return out


if __name__ == "__main__":
    r = evaluar(MEMBERS0)
    print(f"{len(MEMBERS0)} miembros  masa {r['masa']:.1f} kg  K_tors {r['K_tors']:,.0f}")
    for c, v in r["fs"].items():
        print(f"  {c}: FS {v:.2f}  en {r['peor'].get(c, '')}")
