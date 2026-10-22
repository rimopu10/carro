# -*- coding: utf-8 -*-
"""
CARGAS DE SUSPENSIÓN en el FEM del chasis.

Hasta ahora el FEM sostenía el chasis con apoyos fijos en las torres y los pivotes (fem_chasis._sup): las ruedas eran
"paredes", así que los tubos junto a ellas no veían su carga real. Aquí las fuerzas entran como entran en el carro:

    parche de contacto -> mangueta -> brazos / tirante de dirección / amortiguador -> ANCLAJES del chasis

  1. Reparto de las fuerzas de piso (4 parches) para cada caso (n = factor de carga por peso, como LC1/LC3/LC4).
  2. Equilibrio de cuerpo rígido de cada rueda con la cinemática REAL (puntos duros de suspension_delantera.py /
     suspension_trasera.py): delantera = mangueta + 2 horquillas + tirante + coilover (8 incógnitas, 8 ecuaciones);
     trasera = brazo tirado (1 incógnita de amortiguador + reacción del pivote, que lleva momento por la base de 150 mm).
  3. Las reacciones se aplican al chasis en el nodo del tubo que recibe cada ménsula (+ momento por la excentricidad).
  4. El chasis se resuelve libre en equilibrio (alivio de inercia): cargas del piso + peso/inercia de TODAS las masas,
     con 6 apoyos mínimos cuyas reacciones deben salir ~0 (es la prueba de que el reparto cierra).

Casos:  S1 bache 3 g · S2 frenada 1 g · S3 curva 1 g · S4 bache de 3 g en UNA rueda delantera (la otra tres a 1 g)

    python calculos/cargas_suspension.py          # tablas de cargas de ménsula + FS del chasis
"""
import os as _os
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    _os.environ.setdefault(_v, "1")
import contextlib
import io
import sys

import numpy as np

HERE = _os.path.dirname(_os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

with contextlib.redirect_stdout(io.StringIO()):          # estos módulos imprimen y regeneran sus informes
    import fem_chasis as F
    import suspension_delantera as SD
    import suspension_trasera as ST

G = 9.81
GV = np.array([0.0, -G, 0.0])
FY = F.FY


def mz(p):
    """espejo en z (lado izquierdo z>0 -> derecho)."""
    return np.array([p[0], p[1], -p[2]], float)


# ------------------------------------------------------------------------------------------ geometría de las ruedas
R_F, R_R = SD.R_RUEDA, ST.R_RUEDA
SEN_CAMBER = np.sin(np.radians(-SD.CAMBER_EST))
PARCHE = {   # punto de contacto con el piso; el camber de -1 deg corre el parche hacia afuera R*sen(1 deg)
    "FL": np.array([SD.W0[0], 0.0, SD.W0[2] + R_F * SEN_CAMBER]),
    "RL": np.array([ST.EJE0[0], 0.0, ST.EJE0[2]]),
}
PARCHE["FR"], PARCHE["RR"] = mz(PARCHE["FL"]), mz(PARCHE["RL"])
CENTRO = {"FL": np.array(SD.W0), "RL": np.array(ST.EJE0)}
CENTRO["FR"], CENTRO["RR"] = mz(CENTRO["FL"]), mz(CENTRO["RL"])
M_NOSUSP = {"FL": SD.M_NOSUSP, "FR": SD.M_NOSUSP, "RL": ST.M_NOSUSP, "RR": ST.M_NOSUSP}
RUEDAS = ("FL", "FR", "RL", "RR")


def _u(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def _reaccion_bisagra(A, B, cargas, frac=0.5):
    """Brazo articulado en A y B (bujes). `cargas` = [(punto, fuerza sobre el brazo)]. Devuelve (R_A, R_B): fuerza que el
    CHASIS hace sobre el brazo en cada buje. Equilibrio de fuerzas y momentos. La componente AXIAL (a lo largo del eje de los
    pivotes) es hiperestática con bujes esféricos: depende de su rigidez. `frac` = fracción que toma el buje A (0..1); 0.5 es
    el reparto simétrico y 0 / 1 los extremos (auditoría 2026-10-21: las cargas de LA1/UA1/UA2 varían hasta ±60% con esto)."""
    A, B = np.asarray(A, float), np.asarray(B, float)
    u = _u(B - A)
    Ftot = sum((f for p, f in cargas), np.zeros(3))
    Mtot = sum((np.cross(np.asarray(p, float) - A, f) for p, f in cargas), np.zeros(3))
    # incógnitas RA(3), RB(3):  RA + RB = -Ftot ;  (B-A) x RB = -Mtot ;  RA.u = frac * (-Ftot.u)
    M = np.zeros((7, 6))
    M[0:3, 0:3] = np.eye(3)
    M[0:3, 3:6] = np.eye(3)
    S = np.array([[0, -(B - A)[2], (B - A)[1]], [(B - A)[2], 0, -(B - A)[0]], [-(B - A)[1], (B - A)[0], 0]])
    M[3:6, 3:6] = S
    M[6, 0:3] = u
    rhs = np.r_[-Ftot, -Mtot, frac * float(-Ftot @ u)]
    x, *_ = np.linalg.lstsq(M, rhs, rcond=None)
    return x[:3], x[3:]


def rueda_delantera(lado, P, Fu, frac=(0.5, 0.5)):
    """Equilibrio de una rueda delantera. P: fuerza del piso en el parche; Fu: peso+inercia de la masa no suspendida
    (en el centro de rueda). Devuelve dict anclaje -> (punto, fuerza SOBRE EL CHASIS) y las fuerzas internas."""
    s = (lambda p: np.asarray(p, float)) if lado == "L" else mz
    LA1, LA2, UA1, UA2 = s(SD.LA1), s(SD.LA2), s(SD.UA1), s(SD.UA2)
    LBJ, UBJ, TR, RACK = s(SD.LBJ0), s(SD.UBJ0), s(SD.TR0), s(SD.RACK)
    SUP, INF = s(SD.SHK_SUP), s(SD.SHK_INF0)
    pp, rw = PARCHE["F" + lado], CENTRO["F" + lado]
    t = _u(RACK - TR)                      # F_tie > 0 = tirante en tracción; fuerza sobre la mangueta hacia la cremallera
    sa = _u(INF - SUP)                     # F_s > 0 = amortiguador comprimido; fuerza sobre el brazo, lejos de la torre
    uL, uU = _u(LA2 - LA1), _u(UA2 - UA1)
    # x = [F_LBJ(3), F_UBJ(3), F_tie, F_s]; F_LBJ, F_UBJ = fuerza de cada brazo sobre la mangueta
    A = np.zeros((8, 8))
    b = np.zeros(8)
    A[0:3, 0:3] = np.eye(3)
    A[0:3, 3:6] = np.eye(3)
    A[0:3, 6] = t
    b[0:3] = -(P + Fu)

    def X(v):
        return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    A[3:6, 3:6] = X(UBJ - LBJ)
    A[3:6, 6] = np.cross(TR - LBJ, t)
    b[3:6] = -(np.cross(pp - LBJ, P) + np.cross(rw - LBJ, Fu))
    # brazo inferior: momento sobre su eje = 0 (fuerza de la mangueta es -F_LBJ sobre el brazo)
    A[6, 0:3] = np.cross(LBJ - LA1, np.array([1, 0, 0])) @ uL * np.array([1, 0, 0]) \
        + np.cross(LBJ - LA1, np.array([0, 1, 0])) @ uL * np.array([0, 1, 0]) \
        + np.cross(LBJ - LA1, np.array([0, 0, 1])) @ uL * np.array([0, 0, 1])
    A[6, 0:3] *= -1.0
    A[6, 7] = np.dot(np.cross(INF - LA1, sa), uL)
    # brazo superior: momento de -F_UBJ sobre su eje = 0
    for k in range(3):
        e = np.zeros(3)
        e[k] = 1.0
        A[7, 3 + k] = -np.dot(np.cross(UBJ - UA1, e), uU)
    x = np.linalg.solve(A, b)
    F_L, F_U, F_tie, F_s = x[0:3], x[3:6], x[6], x[7]
    # reacciones de los brazos (el chasis sobre el brazo) -> sobre el chasis es lo contrario
    RL1, RL2 = _reaccion_bisagra(LA1, LA2, [(LBJ, -F_L), (INF, F_s * sa)], frac[0])
    RU1, RU2 = _reaccion_bisagra(UA1, UA2, [(UBJ, -F_U)], frac[1])
    out = {
        "LA1": (LA1, -RL1), "LA2": (LA2, -RL2), "UA1": (UA1, -RU1), "UA2": (UA2, -RU2),
        "AMORT": (SUP, -F_s * sa), "DIREC": (RACK, -F_tie * t),
    }
    return out, dict(F_s=F_s, F_tie=F_tie, F_LBJ=F_L, F_UBJ=F_U)


def rueda_trasera(lado, P, Fu):
    """Brazo tirado. Incógnitas: F_s (amortiguador), reacción del pivote (3 fuerzas + momentos Mx, My por la base)."""
    s = (lambda p: np.asarray(p, float)) if lado == "L" else mz
    PIV, SUP, INF = s(ST.PIV), s(ST.SHK_SUP), s(ST.SHK_INF0)
    pp, rw = PARCHE["R" + lado], CENTRO["R" + lado]
    sa = _u(INF - SUP)
    # x = [F_s, R(3), Mx, My]   (R = fuerza del chasis sobre el brazo; M = par del chasis sobre el brazo)
    A = np.zeros((6, 6))
    b = np.zeros(6)
    A[0:3, 0] = sa
    A[0:3, 1:4] = np.eye(3)
    b[0:3] = -(P + Fu)
    A[3:6, 0] = np.cross(INF - PIV, sa)
    A[3, 4] = 1.0
    A[4, 5] = 1.0
    b[3:6] = -(np.cross(pp - PIV, P) + np.cross(rw - PIV, Fu))
    x = np.linalg.solve(A, b)
    F_s, R, M = x[0], x[1:4], np.array([x[4], x[5], 0.0])
    out = {"PIVOTE": (PIV, -R, -M), "AMORT": (SUP, -F_s * sa)}
    return out, dict(F_s=F_s)


# ------------------------------------------------------------------------------------------ chasis con anclajes
# (clave, punto del lado izquierdo, tubo donde se suelda la ménsula (lado L, lado R))
ANCLAJES_F = [
    ("LA1", ("fb_loL", "fb_loR"), ("fb_loL", "fb_loR")),
    ("LA2", ("fb_loL", "fx_loL"), ("fb_loR", "fx_loR")),
    ("UA1", ("fb_loL", "fb_hiL"), ("fb_loR", "fb_hiR")),
    ("UA2", ("fx_loL", "fx_hiL"), ("fx_loR", "fx_hiR")),
    ("AMORT", ("fx_hiL", "fx_hiR"), ("fx_hiL", "fx_hiR")),
    ("DIREC", ("fb_loL", "fb_hiL"), ("fb_loR", "fb_hiR")),   # HIPÓTESIS: la cremallera se ancla al poste del bulkhead
]


def _en_segmento(p, a, b, tol=1e-3):
    ab = b - a
    t = float((p - a) @ ab / (ab @ ab))
    return abs(np.linalg.norm(p - (a + t * ab))) < tol and -tol <= t <= 1 + tol, t


def preparar(miembros0):
    """Devuelve (miembros, nodos_ancla): parte los tubos que reciben ménsula en el punto de anclaje (proyección del punto
    duro sobre el tubo) y registra el nodo. nodos_ancla[(rueda, clave)] = (nombre_nodo, punto_duro, excentricidad)."""
    miembros = [(a, b, sec, (tag, i)) for i, (a, b, sec, tag) in enumerate(miembros0)]   # el tag lleva el índice del tubo original
    nodos = {}
    cont = 0
    for lado in ("L", "R"):
        for clave, hL, hR in ANCLAJES_F:
            host = hL if lado == "L" else hR
            punto = {"LA1": SD.LA1, "LA2": SD.LA2, "UA1": SD.UA1, "UA2": SD.UA2, "AMORT": SD.SHK_SUP, "DIREC": SD.RACK}[clave]
            p = np.asarray(punto, float) if lado == "L" else mz(punto)
            hA, hB = F.NODES[host[0]], F.NODES[host[1]]
            ab = hB - hA
            t = float(np.clip((p - hA) @ ab / (ab @ ab), 0.0, 1.0))      # fuera del tubo: la ménsula sale del nodo extremo
            q = hA + t * ab
            nombre = next((n for n in F.NODES if np.linalg.norm(F.NODES[n] - q) < 1e-3), None)
            if nombre is None:
                nombre = f"an{clave}{lado}"
                F.registrar_nodo(nombre, q)
            if not any(nombre in (a, b) for a, b, s, tag in miembros):      # nodo sin tubos (nuevo o de una corrida anterior): partir
                for i, (a, b, s, tag) in enumerate(miembros):
                    if a in F.NODES and b in F.NODES and _en_segmento(F.NODES[a], hA, hB)[0] and _en_segmento(F.NODES[b], hA, hB)[0]:
                        ok, tt = _en_segmento(q, F.NODES[a], F.NODES[b])
                        if ok and 1e-6 < tt < 1 - 1e-6:
                            miembros[i:i + 1] = [(a, nombre, s, tag), (nombre, b, s, tag)]
                            break
                else:
                    raise RuntimeError(f"no encontré el tubo {host} para el anclaje {clave}{lado}")
            existente = nombre
            nodos[(lado, "F", clave)] = (existente, p, p - q)
    for lado in ("L", "R"):
        piv = np.asarray(ST.PIV, float) if lado == "L" else mz(ST.PIV)
        nodos[(lado, "R", "PIVOTE")] = ("ta" + lado, piv, piv - F.NODES["ta" + lado])     # la ménsula sale del riel (analisis_chasis: ta z=0.488)
        nodos[(lado, "R", "AMORT")] = ("coil" + lado, np.asarray(ST.SHK_SUP, float) if lado == "L" else mz(ST.SHK_SUP), np.zeros(3))
    return miembros, nodos


# ------------------------------------------------------------------------------------------ equilibrio global
import masas_modelo as MM


def masas_todas(miembros):
    """Masas puntuales: las suspendidas (nodos del chasis, F._masas), las que se elevan a la altura de su CG (masas_modelo.ELEVACION: ocupantes,
    butacas, piel, electrónica, varios y la PILA de la batería; nombre `<nodo>_e<k>`: la fuerza se aplica al nodo con el momento F x h) y las 4 no
    suspendidas en el centro de rueda. Auditoría 2026-10-21: antes todo pesaba a la altura del nodo (CG de 0.27 m contra 0.40 del presupuesto)."""
    pts = []
    usar_elev = MM.fijas(F.NODES) is not None          # sólo con el presupuesto por componente (diseño del rediseño)
    for n, m in F._masas(miembros).items():
        resto = m
        if usar_elev:
            for k, (kg, dy) in enumerate(MM.elevadas(n)):
                pts.append((F.NODES[n] + np.array([0.0, dy, 0.0]), kg, f"{n}_e{k}"))
                resto -= kg
        pts.append((F.NODES[n], resto, n))
    pts += [(CENTRO[w], M_NOSUSP[w], "rueda" + w) for w in RUEDAS]
    return pts


def propiedades(pts):
    M = sum(m for _, m, _ in pts)
    cg = sum(m * p for p, m, _ in pts) / M
    I = np.zeros((3, 3))
    for p, m, _ in pts:
        d = p - cg
        I += m * (d @ d * np.eye(3) - np.outer(d, d))
    return M, cg, I


def reparto_piso(n, cg, M):
    """Fuerzas del piso en los 4 parches para un caso de carga n=(nx,ny,nz) (factor por peso, fuerza = m g n sobre cada
    masa): P_i = Fz_i (lx, 1, lz), Fz_i de mínima norma que cierra fuerzas y momentos."""
    B = M * G * np.asarray(n, float)
    lam = np.array([B[0] / B[1], 1.0, B[2] / B[1]])
    A = [np.ones(4)] + [np.array([np.cross(PARCHE[w] - cg, lam)[k] for w in RUEDAS]) for k in range(3)]
    A = np.array(A)
    rhs = np.r_[-B[1], 0.0, 0.0, 0.0]
    fz, *_ = np.linalg.lstsq(A, rhs, rcond=None)
    return {w: fz[i] * lam for i, w in enumerate(RUEDAS)}


def caso_cargas(nombre, miembros, nodos, pts, M, cg, I, P, frac=(0.5, 0.5)):
    """P: dict rueda -> fuerza del piso. Alivio de inercia + equilibrio de cada rueda. Devuelve vector de fuerzas del
    chasis (NDOF), dict de anclajes y de fuerzas internas."""
    Ptot = sum(P.values())
    a0 = GV + Ptot / M
    Mom = sum(np.cross(PARCHE[w] - cg, P[w]) for w in RUEDAS)
    alfa = np.linalg.solve(I, Mom)
    Fv = np.zeros(F.NDOF)
    fu = {}
    for p, m, n in pts:
        d = p - cg
        f = m * (GV - a0 - np.cross(alfa, d))
        if n.startswith("rueda"):
            fu[n[5:]] = f
        elif "_e" in n and n.rsplit("_e", 1)[1].isdigit():   # masa elevada: fuerza en el nodo + momento por la altura de su CG
            nodo, k = n.rsplit("_e", 1)
            dy = MM.elevadas(nodo)[int(k)][1]
            i0 = 6 * F.IDX[nodo]
            Fv[i0:i0 + 3] += f
            Fv[i0 + 3:i0 + 6] += np.cross(np.array([0.0, dy, 0.0]), f)
        else:
            Fv[6 * F.IDX[n]:6 * F.IDX[n] + 3] += f
    ancl, interno = {}, {}
    for w in RUEDAS:
        lado = w[1]
        if w[0] == "F":
            o, i = rueda_delantera(lado, P[w], fu[w], frac)
        else:
            o, i = rueda_trasera(lado, P[w], fu[w])
        interno[w] = i
        i["momentos"] = {}
        for clave, v in o.items():
            nodo, punto, exc = nodos[(lado, w[0], clave)]
            f = v[1]
            m_ = np.cross(exc, f) if len(v) == 2 else v[2]
            if len(v) == 3:
                m_ = v[2] + np.cross(exc, f)
            ancl[(w, clave)] = f
            i["momentos"][clave] = np.array(v[2]) if len(v) == 3 else np.zeros(3)
            i0 = 6 * F.IDX[nodo]
            Fv[i0:i0 + 3] += f
            Fv[i0 + 3:i0 + 6] += m_
    return Fv, ancl, interno, dict(a0=a0, alfa=alfa)


def apoyos_minimos():
    """Isostático: noseL x,y,z; tailL y,z; noseR y. Las reacciones deben salir ~0 (cuerpo en equilibrio)."""
    f = F.fix
    return f("noseL", [0, 1, 2]) + f("tailL", [1, 2]) + f("noseR", [1])


def modo_nulo(cg, n=(0, -1, 0)):
    """Dirección de carga vertical que no cambia ni la suma ni los momentos: FL+RR contra FR+RL (la alabeo del chasis).
    El reparto de mínima norma lo deja en cero; aquí se agrega a propósito (torsión diagonal)."""
    B = M_TOT_G * np.asarray(n, float)
    lam = np.array([B[0] / B[1], 1.0, B[2] / B[1]])
    A = np.array([np.ones(4)] + [np.array([np.cross(PARCHE[w] - cg, lam)[k] for w in RUEDAS]) for k in range(3)])
    v = np.linalg.svd(A)[2][-1]
    return v / np.max(np.abs(v))


M_TOT_G = 690.0 * G
ALABEO_N = 750.0           # N por rueda de carga diagonal (~17% de la carga de esquina)
EXTREMOS_AXIALES = ((0.0, 0.0), (1.0, 1.0), (0.0, 1.0), (1.0, 0.0))


def casos(cg, M):
    """dict nombre -> (fuerzas del piso por rueda, (frac axial inferior, frac axial superior))."""
    base = reparto_piso((0, -1, 0), cg, M)
    s4 = {w: base[w].copy() for w in RUEDAS}
    s4["FL"] = s4["FL"] * 3.0
    s1 = reparto_piso((0, -3, 0), cg, M)
    v = modo_nulo(cg)
    s6 = {w: s1[w] + np.array([0.0, ALABEO_N * v[i], 0.0]) for i, w in enumerate(RUEDAS)}
    nominal = {
        "S1 bache 3 g": s1,
        "S2 frenada 1 g": reparto_piso((-1, -1, 0), cg, M),
        "S3 curva 1 g": reparto_piso((0, -1, 1), cg, M),
        "S4 bache 3 g en rueda del. izq.": s4,
        "S5 bache 3 g + curva 1 g": reparto_piso((0, -3, 1), cg, M),
        "S6 bache 3 g con alabeo diagonal": s6,
    }
    out = {n: (P, (0.5, 0.5)) for n, P in nominal.items()}
    for n in ("S1 bache 3 g", "S4 bache 3 g en rueda del. izq.", "S5 bache 3 g + curva 1 g", "S6 bache 3 g con alabeo diagonal"):
        for fr in EXTREMOS_AXIALES:
            out[f"{n} [axial {fr[0]:.0f}/{fr[1]:.0f}]"] = (nominal[n], fr)
    return out


def evaluar_suspension(miembros0, verbose=False):
    """-> dict(caso -> dict(fs_min, peor, fs_miembro{(a,b):FS}, pandeo{(a,b):FS}, reaccion_residual, anclajes, interno, P))"""
    miembros, nodos = preparar(miembros0)
    usados = {n for a, b, s, t in miembros for n in (a, b)}
    flotan = [v[0] for v in nodos.values() if v[0] not in usados]
    if flotan:
        raise RuntimeError(f"anclajes sin tubo (la carga se perdería): {flotan}")
    pts = masas_todas(miembros)
    M, cg, I = propiedades(pts)
    K, elems = F.ensamblar(miembros)
    fixed = apoyos_minimos()
    res = {}
    for nom, (P, frac) in casos(cg, M).items():
        Fv, ancl, interno, rb = caso_cargas(nom, miembros, nodos, pts, M, cg, I, P, frac)
        U = F._resolver_multi(K, Fv.reshape(-1, 1), fixed)[:, 0]
        R = (K @ U - Fv)[fixed]
        fs, pand, peor, mn = {}, {}, "", np.inf
        for e in elems:
            sig, fsb = F.esfuerzo_max(e, U)
            f = FY / sig if sig > 0 else np.inf
            fs[(e["a"], e["b"])] = f
            pand[(e["a"], e["b"])] = fsb
            if f < mn:
                mn, peor = f, f"{e['a']}-{e['b']}"
        res[nom] = dict(fs_min=mn, peor=peor, fs=fs, pandeo=pand, residual=float(np.max(np.abs(R))),
                        anclajes=ancl, interno=interno, P=P, rb=rb, U=U, nodos=nodos)
    return dict(casos=res, miembros=miembros, M=M, cg=cg, nodos=nodos)


_VIGENTE = None


def cargar_vigente():
    """Chasis vigente (chasis_rediseno.json) dentro del FEM reutilizable. fem_chasis carga el diseño BASE (su __file__ falso no
    encuentra el JSON): se replica aquí lo que hace analisis_chasis.py / rediseno_chasis.py."""
    import json
    global _VIGENTE
    if _VIGENTE is not None:           # F.mover_masa hace pop: una segunda carga en el mismo proceso lanzaba KeyError
        return list(_VIGENTE)
    d = json.load(open(_os.path.join(HERE, "chasis_rediseno.json"), encoding="utf-8"))

    def sec(nombre):
        t, dims = nombre.split(" ", 1)
        v = [float(x) for x in dims.split("x")]
        return F.sec_ptr(v[0] / 1000, v[2] / 1000) if t == "PTR" else F.sec_red(v[0] / 1000, v[1] / 1000)
    usados = {n for m in d["miembros"] for n in m[:2]}
    for n, p in d["nodos_nuevos"].items():
        if n in usados:
            F.registrar_nodo(n, p)
    for n, p in d.get("nodos_movidos", {}).items():
        F.NODES[n] = np.array(p, float)
    for o, t in d.get("masas_mover", {}).items():
        F.mover_masa(o, t)
    _VIGENTE = [(a, b, sec(sn), tag) for a, b, sn, tag in d["miembros"]]
    return list(_VIGENTE)


def escribir_md(out, ruta):
    """docs/cargas-suspension.md: cargas de diseño de cada ménsula y FS del chasis, regenerado desde el cálculo."""
    M, cg = out["M"], out["cg"]
    L = ["# Cargas de suspensión y ménsulas", "",
         "Generado por `calculos/cargas_suspension.py` (no editar a mano). Las fuerzas del piso pasan por la mangueta, los brazos,",
         "el amortiguador y la cremallera hasta cada anclaje del chasis; el chasis se resuelve libre en equilibrio (reacciones de",
         "los apoyos mínimos = 0).", "",
         f"Masa total {M:.0f} kg (564 suspendida + 126 no suspendida) · CG ({cg[0]:.2f}, {cg[1]:.2f}) m · "
         + "reparto estático por esquina: " + ", ".join(f"{w} {reparto_piso((0, -1, 0), cg, M)[w][1] / G:.0f} kg" for w in RUEDAS),
         "", "## Factor de seguridad del chasis con las ruedas pasando por los brazos", "",
         "| Caso | FS mínimo | Tubo crítico |", "|---|---|---|"]
    base = {n: r for n, r in out["casos"].items() if "[axial" not in n}
    for nom, r in base.items():
        L.append(f"| {nom} | {r['fs_min']:.2f} | `{r['peor']}` |")
    var = {n: r for n, r in out["casos"].items() if "[axial" in n}
    if var:
        n_, r_ = min(var.items(), key=lambda kv: kv[1]["fs_min"])
        L.append(f"| **Peor extremo del reparto axial de las bisagras** ({n_}) | {r_['fs_min']:.2f} | `{r_['peor']}` |")
    L += ["", "## Carga de diseño de cada ménsula (lado izquierdo; el derecho es el espejo)", "",
          "Resultante en N, máximo de los 4 casos, en el punto duro. `exc.` = distancia del punto duro al eje del tubo que la",
          "recibe (la ménsula transmite además el momento F·exc). Dimensionar la soldadura y la placa con FS ≥ 2 sobre este valor. El valor es el MÁXIMO de",
          "todos los casos, incluidos los extremos del reparto axial de las bisagras (hiperestático: depende de la rigidez de los bujes) y el alabeo diagonal.", "",
          "| Anclaje | Resultante máx. (N) | Caso | Nodo del chasis | exc. (mm) |", "|---|---|---|---|---|"]
    nombres = {"AMORT": "Torre del amortiguador", "LA1": "Brazo inf., pivote delantero", "LA2": "Brazo inf., pivote trasero",
               "UA1": "Brazo sup., pivote delantero", "UA2": "Brazo sup., pivote trasero",
               "DIREC": "Cremallera (soporte, HIPÓTESIS)", "PIVOTE": "Brazo trasero, pivote (+ momentos Mx, My)"}
    for w in ("FL", "RL"):
        for k in sorted({k for (ww, k) in out["casos"]["S1 bache 3 g"]["anclajes"] if ww == w}):
            vals = {nom: float(np.linalg.norm(r["anclajes"][(w, k)])) for nom, r in out["casos"].items()}
            mx = max(vals, key=vals.get)
            nodo, _, exc = out["nodos"][(w[1], w[0], k)]
            nm = nombres.get(k, k) + (" (delantera)" if w == "FL" and k == "AMORT" else " (trasera)" if k == "AMORT" else "")
            L.append(f"| {nm} | {vals[mx]:.0f} | {mx} | `{nodo}` | {np.linalg.norm(exc) * 1000:.0f} |")
    mp = max((float(np.linalg.norm(r["interno"]["RL"]["momentos"]["PIVOTE"])), n) for n, r in out["casos"].items())
    L += ["", f"Pivote trasero: además de la fuerza, transmite un MOMENTO de hasta **{mp[0]:.0f} N·m** ({mp[1]}) por la base de 150 mm entre bujes: "
              f"eso son ±{mp[0] / 0.15:.0f} N por buje (vertical/lateral). El brazo se monta entre dos orejas a 6 mm de sus caras; el riel queda 64 mm "
              f"hacia adentro del pivote (nodo ta en z=0.488).", ""]
    L += ["", "## Fuerzas internas (N)", "", "| Caso | Amortiguador del. | Tirante de dirección | Amortiguador tras. |", "|---|---|---|---|"]
    for nom, r in out["casos"].items():
        i = r["interno"]
        L.append(f"| {nom} | {i['FL']['F_s']:.0f} | {i['FL']['F_tie']:.0f} | {i['RL']['F_s']:.0f} |")
    L += ["", "## Supuestos y límites", "",
          "- Fuerzas de piso: reparto con Fx, Fy proporcionales a Fz (frenado y curva ideales) y Fz de mínima norma; el exceso se",
          "  cierra con aceleración de cuerpo rígido (alivio de inercia). S4 pone 3 g en una rueda delantera y 1 g en las otras.",
          "- Masa no suspendida concentrada en el centro de rueda (18 kg delante, 45 kg atrás); sin su inercia de rotación.",
          "- Cinemática en posición de reposo (sin recorrido, sin ángulo de giro).",
          "- El soporte de la cremallera se supone en el poste del bulkhead, a 82 mm del eje: AÚN NO está diseñado.",
          "- Las ménsulas no están modeladas como sólidos: cada una es un punto rígido con su excentricidad.",
          "- El CG sale de las masas del FEM (carga repartida por longitud de tubo): da 45% de peso delante, no el 38% con que se",
          "  calcularon los resortes. Hay que fijar dónde va la masa real (batería, controladores) y recalcular resortes."]
    open(ruta, "w", encoding="utf-8").write(chr(10).join(L) + chr(10))


def main():
    out = evaluar_suspension(cargar_vigente())
    escribir_md(out, _os.path.join(HERE, "..", "docs", "cargas-suspension.md"))
    M, cg = out["M"], out["cg"]
    print(f"Masa total {M:.0f} kg (suspendida 564 + no suspendida 126) · CG ({cg[0]:.3f}, {cg[1]:.3f}, {cg[2]:+.3f}) m")
    print(f"Reparto estático por esquina: " + "  ".join(
        f"{w} {reparto_piso((0, -1, 0), cg, M)[w][1] / G:.0f} kg" for w in RUEDAS))
    print()
    for nom, r in out["casos"].items():
        print(f"== {nom} ==")
        print("  fuerzas de piso (N)  " + "  ".join(f"{w}: vert {r['P'][w][1]:6.0f} long {r['P'][w][0]:6.0f} lat {r['P'][w][2]:6.0f}"
                                                      for w in RUEDAS))
        print(f"  acel. del cuerpo: a0 = ({r['rb']['a0'][0]/G:+.2f}, {r['rb']['a0'][1]/G:+.2f}, {r['rb']['a0'][2]/G:+.2f}) g   "
              f"reacción residual de apoyos: {r['residual']:.1f} N")
        print(f"  FS mínimo del chasis: {r['fs_min']:.2f}  en {r['peor']}")
    return out


if __name__ == "__main__":
    main()
