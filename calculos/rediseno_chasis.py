# -*- coding: utf-8 -*-
"""
REDISEÑO DEL CHASIS: el mismo carro, con el hueco de la puerta libre, más ligero y con la
carga puesta donde trabaja. Estructura de tierra (ground structure) + poda + dimensionado.

Qué hace
  1. Quita lo que bloquea la entrada (calculos/hueco_puerta.py) y los volúmenes del piloto.
  2. Parte del chasis vigente + TODOS los tubos candidatos que no entran a un volumen prohibido
     (hueco de puerta, piernas, torso, cabeza) y agrega nodos en el centro del piso (en el vigente
     las dos X del piso se cruzaban en el aire sin tocarse).
  3. Poda: intenta quitar cada tubo (L/R juntos, por simetría) y lo quita si TODO sigue cumpliendo.
  4. Dimensiona: baja cada tubo por el catálogo mientras todo siga cumpliendo.
  5. Repite 3-4 hasta que no se pueda mover nada.

Restricciones (las mismas de siempre, más una)
  FS fluencia >= 2.0 en bache 3g, frenada 1g y curva 1g · FS pandeo Euler >= 2.0
  FS volcadura (2.0W vert + 0.75W lat) >= 1.5 · K torsional >= K_MIN
  Pisos: célula en redondo >= RED 44.5x2.1 · barra de cinturones >= PTR 38x38x1.9 ·
  cuna de batería >= PTR 32x32x1.9 · el resto >= PTR 25x25x1.5.
  NO se tocan nodos de suspensión/anclajes ni la posición de la célula (eso ya está medido contra la piel).

    python calculos/rediseno_chasis.py        # escribe calculos/chasis_rediseno.json y el informe
"""
import os as _os
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    _os.environ.setdefault(_v, "1")   # sistemas chicos: con muchos hilos BLAS tarda 60x más
import itertools
import json
import os
import sys

import numpy as np
from matplotlib.path import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ["CHASIS_BASE"] = "1"        # partir del diseño anterior, no del rediseño ya aplicado
import fem_chasis as F                                    # noqa: E402
import hueco_puerta as HP                                 # noqa: E402
import buck_piloto as BK                                  # noqa: E402
import puertas as PU                                      # noqa: E402

K_MIN = float(sys.argv[1]) if len(sys.argv) > 1 else 8000.0   # N·m/° (doc maestro pide >4,000; el vigente da 14,177)
FS_MIN, FS_VUELCO, FS_PANDEO = 2.0, 1.5, 2.0
FS_CABECERA = 1.3      # volcadura cargando la cabecera (el diseño anterior daba 1.30)
FS_TORSION = 2.0       # par de 4,500 N·m (bache en una rueda a 3g; el anterior daba 2.25)
FS_PUERTA = 2.0        # LC7: puertas abiertas a 65 grados (3 g + viento + amortiguador)
if os.environ.get("MISMA_RESISTENCIA"):   # variante: no peor que el diseño anterior en NINGÚN caso
    FS_MIN, FS_VUELCO, FS_CABECERA, FS_TORSION = 2.05, 1.64, 1.30, 2.25
OUT_JSON = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "chasis_rediseno.json")

# ---------------------------------------------------------------- catálogo
def ptr(b, t):
    s = F.sec_ptr(b / 1000, t / 1000); s["kg_m"] = s["A"] * F.RHO; s["tipo"] = "PTR"; return s

def red(d, t):
    s = F.sec_red(d / 1000, t / 1000); s["kg_m"] = s["A"] * F.RHO; s["tipo"] = "RED"; return s

# Pared mínima 1.9 mm: con MIG de principiante la de 1.5 se perfora (auditoría estructural 2026-10-12)
CAT_PTR = sorted([ptr(25, 1.9), ptr(32, 1.9), ptr(38, 1.9), ptr(38, 3.0), ptr(44, 1.9)],
                 key=lambda s: s["kg_m"])
CAT_RED = sorted([red(44.5, 2.1), red(44.5, 3.2), red(50.8, 2.1), red(50.8, 3.2), red(57.2, 2.1),
                  red(57.2, 3.2)], key=lambda s: s["kg_m"])
POR_NOMBRE = {s["nombre"]: s for s in CAT_PTR + CAT_RED}
for _s in (ptr(25, 1.5), ptr(32, 1.5), ptr(38, 1.5)):        # secciones del diseño anterior (sólo lectura)
    POR_NOMBRE.setdefault(_s["nombre"], _s)


def sec_por_nombre(n):
    if n in POR_NOMBRE:
        return POR_NOMBRE[n]
    raise KeyError(n)

# Pisos por función. Regla heredada: un tubo no se optimiza contra un análisis que no incluye su caso.
#  cell: célula/arcos/techo/pilar A -> RED 50.8x2.1 (el mínimo FIA para arco de acero dulce es 50x2.0 ó
#        45x2.5; con 44.5x2.1 el propio código advertía que 2.1 mm es el límite bajo para el arco principal)
#  susp: tubos que tocan un anclaje de suspensión: el FEM los toma como apoyos y NO aplica las cargas de
#        la llanta (frenada/curva en el contacto), así que no hay análisis que justifique adelgazarlos
#  belt: barra de cinturones: con arnés a 10 g la 38x1.9 llegaba a 200 MPa (FS 1.2) -> 38x3.0
#  ext : nariz (estructura de choque) y cola -> 32x1.9
PISO = {"cell": "RED 50.8x2.1", "belt": "PTR 38x38x3.0", "batt": "PTR 32x32x1.9",
        "susp": "PTR 38x38x1.9", "ext": "PTR 32x32x1.9", "otro": "PTR 25x25x1.9"}
NODOS_SUSP = {"fb_loL", "fb_loR", "fb_hiL", "fb_hiR", "fx_loL", "fx_loR", "fx_hiL", "fx_hiR", "taL", "taR",
              "coilL", "coilR", "r_loL", "r_loR", "r_hiL", "r_hiR"}
NODOS_EXT = {"noseL", "noseR", "tailL", "tailR"}

# ---------------------------------------------------------------- simetría
SIN_LADO = ("cf1", "cfF", "cf2", "cf3")


def esp(n):
    return n[:-1] + ("R" if n[-1] == "L" else "L") if n[-1] in "LR" and n not in SIN_LADO else n

def mid(m):          # id de miembro (sin orden)
    return frozenset(m[:2])

def espejo(m):
    return frozenset(esp(n) for n in m)

# ---------------------------------------------------------------- nodos nuevos
# Asiento sobre RIELES: dos travesaños (x=1.36 y 1.66, uno bajo cada estación del riel) cargan cada uno la mitad de
# los 90 kg de cada ocupante, en z=±0.31 (donde está el piloto; antes el modelo ponía el peso en mitad del estribo).
# cf2 queda en el travesaño trasero (x=1.66): ahí se cruzan las dos X del piso.
# Bisagras (h1, h2) sobre el riel del espinazo y ancla del amortiguador (sa) en la cabecera: ver puertas.py.
H1, H2, SA = PU.punto_riel(PU.S_H1), PU.punto_riel(PU.S_H2), PU.SA
XF, XR = 1.36, 1.66
NUEVOS = {
    "cf1": (1.10, 0.16, 0.0), "cfF": (XF, 0.16, 0.0), "cf2": (XR, 0.16, 0.0), "cf3": (2.02, 0.16, 0.0),
    "seatFL": (XF, 0.16, 0.591), "seatFR": (XF, 0.16, -0.591),
    "smFL": (XF, 0.16, 0.31), "smFR": (XF, 0.16, -0.31),
    "smRL": (XR, 0.16, 0.31), "smRR": (XR, 0.16, -0.31),
    "h1L": tuple(float(v) for v in H1), "h2L": tuple(float(v) for v in H2), "saL": tuple(float(v) for v in SA),
    "h1R": (float(H1[0]), float(H1[1]), -float(H1[2])), "h2R": (float(H2[0]), float(H2[1]), -float(H2[2])),
    "saR": (float(SA[0]), float(SA[1]), -float(SA[2])),
}
OBLIGADOS = {"smFL", "smFR", "smRL", "smRR", "seatFL", "seatFR", "h1L", "h2L", "saL", "h1R", "h2R", "saR"}
MOVIDOS = {"seatL": (XR, 0.16, 0.591), "seatR": (XR, 0.16, -0.591)}        # el nodo del estribo pasa al riel trasero
MASAS_MOVER = {"seatL": {"smFL": 0.5, "smRL": 0.5}, "seatR": {"smFR": 0.5, "smRR": 0.5}}
for n, p in NUEVOS.items():
    F.registrar_nodo(n, p)
NODES = F.NODES
for n, p in MOVIDOS.items():
    NODES[n] = np.array(p, float)
for o, t in MASAS_MOVER.items():
    F.mover_masa(o, t)

PROHIBIDOS = set()      # miembros (ids) vetados tras un intento: se llena en main() cuando un nodo queda saturado
DIAG_ARCO = {frozenset(("mh_loL", "mh_hiR")), frozenset(("mh_loR", "mh_hiL"))}   # X del arco: se puede probar quitarla

# ---------------------------------------------------------------- base: vigente sin bloqueos, con piso partido
BLOQUEAN = {frozenset(("dash_hiL", "mh_loL")), frozenset(("dash_hiR", "mh_loR"))}
# la cuna de batería repetía el eje del riel (bat_f-ta-bat_r están alineados): no se pueden soldar los dos
DUPLICADOS = {frozenset(("bat_fL", "bat_rL")), frozenset(("bat_fR", "bat_rR"))}
SPLIT = {  # miembro -> nodos intermedios, en orden desde el primer nodo del miembro en F.MEMBERS0
    frozenset(("dash_loL", "dash_loR")): ["cf1"],
    frozenset(("dash_loL", "mh_loR")): ["cf2"],
    frozenset(("dash_loR", "mh_loL")): ["cf2"],
    frozenset(("dash_loL", "seatL")): ["seatFL"],
    frozenset(("dash_loR", "seatR")): ["seatFR"],
    frozenset(("sp_fL", "sp_rL")): ["h1L", "h2L"],
    frozenset(("sp_fR", "sp_rR")): ["h1R", "h2R"],
    frozenset(("hdrL", "sp_fL")): ["saL"],
    frozenset(("hdrR", "sp_fR")): ["saR"],
}

def clase(a, b, tag, s):
    if tag == "safe" and s["tipo"] == "RED":
        return "cell"
    if tag == "safe":
        return "belt" if {a, b} == {"mh_beltL", "mh_beltR"} else "susp"
    if tag == "batt":
        return "batt"
    if tag == "asiento":
        return "ext"
    if tag == "tors":
        return "otro"
    if a in NODOS_SUSP or b in NODOS_SUSP:
        return "susp"
    if a in NODOS_EXT or b in NODOS_EXT:
        return "ext"
    return "otro"

def base_miembros():
    out = []
    for a, b, s, tag in F.MEMBERS0:
        i = mid((a, b))
        if i in BLOQUEAN or i in DUPLICADOS:
            continue
        s = sec_por_nombre(s["nombre"])
        c0 = clase(a, b, tag, s)
        cat0, ip0 = piso_idx(dict(clase=c0))
        if s["nombre"] not in {x["nombre"] for x in cat0}:
            s = cat0[ip0]                      # sección legada (1.5 mm) -> la mínima del catálogo
        elif next(j for j, x in enumerate(cat0) if x["nombre"] == s["nombre"]) < ip0:
            s = cat0[ip0]                      # por debajo del piso de su clase
        if i in SPLIT:
            cadena = [a] + SPLIT[i] + [b]
            gid = ("cadena", frozenset({i, espejo(tuple(i))}))     # tramos de un MISMO tubo: misma sección
            for p, q in zip(cadena[:-1], cadena[1:]):
                out.append((p, q, s, tag, gid))
        else:
            out.append((a, b, s, tag, None))
    # travesaños de piso bajo las estaciones de los rieles del asiento: estribo -> asiento -> centro
    s32 = sec_por_nombre("PTR 32x32x1.9")
    for lado in ("L", "R"):
        out += [("seatF" + lado, "smF" + lado, s32, "asiento", None), ("smF" + lado, "cfF", s32, "asiento", None),
                ("seat" + lado, "smR" + lado, s32, "asiento", None), ("smR" + lado, "cf2", s32, "asiento", None)]
    return out

# ---------------------------------------------------------------- volúmenes prohibidos
POLI = Path(HP.poligono_encogido())
# cuerpo del piloto (1.75 m) en los 3 puntos del recorrido de los rieles, en ambos asientos
CAPS = []
for _hx in (BK.RIELES[0], BK.NOMINAL["hx"], BK.RIELES[1]):
    for _z in (0.31, -0.31):
        CAPS += BK.capsulas(BK.postura(_hx, BK.NOMINAL["hy"], BK.NOMINAL["recline"]), z=_z)

def bloquea(pa, pb, paso=0.01):
    L = np.linalg.norm(pb - pa)
    P = pa + (pb - pa) * np.linspace(0, 1, max(int(L / paso), 2))[:, None]
    z = np.abs(P[:, 2])
    ap = POLI.contains_points(P[:, :2]) & (z > HP.Z_MIN) & (z < HP.Z_MAX) & (P[:, 0] < HP.X_MAX)
    bateria = (P[:, 0] > 2.08) & (P[:, 0] < 2.66) & (z < 0.47) & (P[:, 1] > 0.17) & (P[:, 1] < 0.45)
    estribo = (P[:, 0] > 1.22) & (P[:, 0] < 1.97) & (z > 0.20) & (z < 0.66) & (P[:, 1] > 0.20) & (P[:, 1] < 0.50)
    nariz = (P[:, 0] > 0.15) & (P[:, 0] < 0.80) & (z < 0.45) & (P[:, 1] > 0.20) & (P[:, 1] < 0.60)
    # parabrisas: franja de 8 cm a cada lado del plano cowl (0.95, 0.65) -> cabecera (1.45, 0.93), entre pilares
    y_ws = 0.65 + 0.56 * (P[:, 0] - 0.95)
    vidrio = (np.abs(P[:, 1] - y_ws) < 0.08) & (P[:, 0] > 0.97) & (P[:, 0] < 1.43) & (z < 0.40)
    columna = (P[:, 0] > 0.97) & (P[:, 0] < 1.30) & (P[:, 2] > 0.20) & (P[:, 2] < 0.42) & (P[:, 1] > 0.40) & (P[:, 1] < 0.78)
    # plano del arco detrás de los asientos: la barra de cinturones lleva los anclajes del arnés y nada más
    plano_arco = (P[:, 0] > 1.98) & (P[:, 0] < 2.06) & (z > 0.12) & (z < 0.42) & (P[:, 1] > 0.30) & (P[:, 1] < 1.00)
    cuerpo = np.zeros(len(P), bool)
    for c in CAPS:
        cuerpo |= BK.dist_punto_capsula(P, c) < 0.0
    return bool((ap | cuerpo | bateria | estribo | nariz | vidrio | columna | plano_arco).any())

# ---------------------------------------------------------------- candidatos
CAB = ["dash_loL", "dash_loR", "dash_hiL", "dash_hiR", "hdrL", "hdrR", "sp_fL", "sp_fR", "sp_rL", "sp_rR",
       "seatL", "seatR", "seatFL", "seatFR", "mh_loL", "mh_loR", "mh_beltL", "mh_beltR", "mh_hiL", "mh_hiR", "bat_fL", "bat_fR",
       "fx_loL", "fx_loR", "fx_hiL", "fx_hiR", "coilL", "coilR", "cf1", "cfF", "cf2", "cf3", "smFL", "smFR", "smRL", "smRR"]

ANGULO_MIN = 20.0       # grados entre dos tubos que llegan al mismo nodo (si no, no hay cómo soldarlos)

def _dir(n, o):
    v = NODES[o] - NODES[n]
    return v / np.linalg.norm(v)

def angulo_ok(a, b, vecinos):
    """vecinos: dict nodo -> lista de nodos unidos. El tubo a-b no debe quedar a < ANGULO_MIN de otro en a ni en b."""
    for n, o in ((a, b), (b, a)):
        for m in vecinos.get(n, []):
            if m == o:
                continue
            c = float(np.clip(np.dot(_dir(n, o), _dir(n, m)), -1, 1))
            if np.degrees(np.arccos(c)) < ANGULO_MIN:
                return False
    return True

def candidatos(existentes):
    ex = set(existentes)
    vec = {}
    for p, q in map(tuple, ex):
        vec.setdefault(p, []).append(q); vec.setdefault(q, []).append(p)
    segs = [(F.NODES[a], F.NODES[b]) for a, b in map(tuple, ex)]
    cand = []
    for a, b in itertools.combinations(CAB, 2):
        i = frozenset((a, b))
        if i in ex or espejo((a, b)) in ex:
            continue
        pa, pb = NODES[a], NODES[b]
        L = np.linalg.norm(pb - pa)
        if not (0.25 < L < 1.8) or bloquea(pa, pb) or not angulo_ok(a, b, vec):
            continue
        # sólo una mitad por simetría; que no pase pegado a otro nodo ni sobre otro tubo
        if (a, b) > (esp(a), esp(b)) and espejo((a, b)) != i:
            continue
        pm = (pa + pb) / 2
        if any(np.linalg.norm(NODES[n] - pm) < 0.05 for n in NODES if n not in (a, b)):
            continue
        if any(np.linalg.norm(np.cross(q2 - q1, pm - q1)) / np.linalg.norm(q2 - q1) < 0.03
               and 0 < np.dot(pm - q1, q2 - q1) / np.dot(q2 - q1, q2 - q1) < 1 for q1, q2 in segs):
            continue
        cand.append((a, b))
    return cand

# ---------------------------------------------------------------- estado
class Diseno:
    """pares simétricos (y cadenas de tramos de UN mismo tubo): pid -> dict(segs, ids, clase, sec, removible, tag)
    Todos los tramos de un pid comparten sección: es lo que permite fusionarlos en la lista de corte."""
    def __init__(self):
        self.p = {}

    def agregar(self, a, b, sec, clase_, removible, tag, grupo=None):
        if grupo is None:
            ids = {mid((a, b)), espejo((a, b))}
            pid = frozenset(ids)
            if pid in self.p:
                return
            segs = [(a, b)] + ([(esp(a), esp(b))] if espejo((a, b)) != mid((a, b)) else [])
            self.p[pid] = dict(segs=segs, clase=clase_, sec=sec, removible=removible, tag=tag, ids=set(ids))
            return
        d = self.p.setdefault(grupo, dict(segs=[], clase=clase_, sec=sec, removible=removible, tag=tag, ids=set()))
        for p, q in ((a, b), (esp(a), esp(b))):
            if frozenset((p, q)) not in d["ids"]:
                d["ids"].add(frozenset((p, q)))
                d["segs"].append((p, q))

    def miembros(self):
        out = []
        for d in self.p.values():
            if d["sec"] is None:
                continue
            for a, b in d["segs"]:
                out.append((a, b, d["sec"], d["tag"]))
        return out

    def copia(self):
        n = Diseno(); n.p = {k: dict(v) for k, v in self.p.items()}; return n


def cumple(res):
    if any(res["fs"][c] < FS_MIN for c in ("LC1", "LC3", "LC4")) or res["fs"]["LC5"] < FS_VUELCO:
        return False
    if res["K_tors"] < K_MIN or res["fs"]["LC5c"] < FS_CABECERA or res["fs"]["LC6"] < FS_TORSION or res["fs"]["LC7"] < FS_PUERTA:
        return False
    if min(res["pandeo"].values(), default=np.inf) < FS_PANDEO or min(res["pandeo5"].values(), default=np.inf) < FS_VUELCO:
        return False
    return True


def conectado(d):
    """Todo nodo original conserva >= 2 miembros; los nuevos 0 o >= 2."""
    deg = {}
    for a, b, s, t in d.miembros():
        deg[a] = deg.get(a, 0) + 1; deg[b] = deg.get(b, 0) + 1
    for n in F.NODES:
        if n in NUEVOS and n not in OBLIGADOS:
            if deg.get(n, 0) == 1:
                return False
        elif deg.get(n, 0) < 2:
            return False
    return True


def evaluar(d):
    return F.evaluar(d.miembros())


def piso_idx(d_):
    cat = CAT_RED if d_["clase"] == "cell" else CAT_PTR
    nombre = PISO[d_["clase"]]
    return cat, next(i for i, s in enumerate(cat) if s["nombre"] == nombre)


def masa_par(d_):
    if d_["sec"] is None:
        return 0.0
    return sum(np.linalg.norm(NODES[b] - NODES[a]) for a, b in map(tuple, d_["ids"])) * d_["sec"]["kg_m"]


def podar(d, log):
    cambio = False
    orden = sorted([k for k, v in d.p.items() if v["removible"] and v["sec"] is not None],
                   key=lambda k: -masa_par(d.p[k]))
    for k in orden:
        prueba = d.copia(); prueba.p[k] = dict(prueba.p[k], sec=None)
        if not conectado(prueba):
            continue
        if cumple(evaluar(prueba)):
            d.p[k] = prueba.p[k]; cambio = True
            log.append(("quitó", sorted(map(sorted, d.p[k]["ids"])), None))
    return cambio


def dimensionar(d, log):
    cambio = False
    orden = sorted([k for k, v in d.p.items() if v["sec"] is not None], key=lambda k: -masa_par(d.p[k]))
    for k in orden:
        cat, ip = piso_idx(d.p[k])
        while True:
            i = next(j for j, s in enumerate(cat) if s["nombre"] == d.p[k]["sec"]["nombre"])
            if i <= ip:
                break
            prueba = d.copia(); prueba.p[k] = dict(prueba.p[k], sec=cat[i - 1])
            if not cumple(evaluar(prueba)):
                break
            d.p[k] = prueba.p[k]; cambio = True
    return cambio


def margenes(res):
    return np.array([res["K_tors"] / K_MIN, res["fs"]["LC1"] / FS_MIN, res["fs"]["LC3"] / FS_MIN,
                     res["fs"]["LC4"] / FS_MIN, res["fs"]["LC5"] / FS_VUELCO,
                     res["fs"]["LC5c"] / FS_CABECERA, res["fs"]["LC6"] / FS_TORSION, min(res["fs"]["LC7"], 1e3) / FS_PUERTA,
                     min(min(res["pandeo"].values(), default=1e3), 1e3) / FS_PANDEO,
                     min(min(res["pandeo5"].values(), default=1e3), 1e3) / FS_VUELCO])


def costo(m0, m1, eps=0.01):
    """Cuánto se acerca el diseño a sus límites (barrera logarítmica): perder margen donde ya
    casi no hay cuesta mucho; perderlo donde sobra, casi nada."""
    return float(np.sum(np.log(np.maximum(m0 - 1, 0) + eps) - np.log(np.maximum(m1 - 1, 0) + eps)))


def movimientos(d):
    out = []
    for k, v in d.p.items():
        if v["sec"] is None:
            continue
        if v["removible"]:
            out.append((k, "quitar"))
        cat, ip = piso_idx(v)
        i = next(j for j, s in enumerate(cat) if s["nombre"] == v["sec"]["nombre"])
        if i > ip:
            out.append((k, "bajar"))
    return out


def aplicar(d, k, mov):
    p = d.copia()
    if mov == "quitar":
        p.p[k] = dict(p.p[k], sec=None)
    else:
        cat, ip = piso_idx(p.p[k])
        i = next(j for j, s in enumerate(cat) if s["nombre"] == p.p[k]["sec"]["nombre"])
        p.p[k] = dict(p.p[k], sec=cat[i - 1])
    return p


def optimizar_barrera(d, log):
    """Voraz perezoso: aplica siempre el movimiento (quitar un par / bajar un escalón) que más masa
    ahorra por unidad de margen gastado, mientras todo siga cumpliendo."""
    import heapq
    res = evaluar(d); m0 = margenes(res); masa0 = res["masa"]
    heap, cuenta = [], 0

    def puntaje(mov_k):
        k, mov = mov_k
        p = aplicar(d, k, mov)
        if mov == "quitar" and not conectado(p):
            return None
        r = evaluar(p)
        if not cumple(r):
            return None
        dm = masa0 - r["masa"]
        return dm / (max(costo(m0, margenes(r)), 0.0) + 0.02), r

    for mk in movimientos(d):
        sc = puntaje(mk)
        if sc:
            heapq.heappush(heap, (-sc[0], cuenta, mk)); cuenta += 1
    it = 0
    while heap:
        neg, _, mk = heapq.heappop(heap)
        k, mov = mk
        if d.p[k]["sec"] is None:
            continue
        # el movimiento puede haber cambiado de sentido (bajar ya no es el mismo escalón)
        if mov == "bajar" and piso_idx(d.p[k])[1] >= next(j for j, s in enumerate(piso_idx(d.p[k])[0]) if s["nombre"] == d.p[k]["sec"]["nombre"]):
            continue
        sc = puntaje(mk)
        if not sc:
            continue
        if heap and sc[0] < 0.7 * (-heap[0][0]):      # voraz perezoso con tolerancia
            heapq.heappush(heap, (-sc[0], cuenta, mk)); cuenta += 1
            continue
        d.p[k] = aplicar(d, k, mov).p[k]
        res = sc[1]; m0 = margenes(res); masa0 = res["masa"]
        it += 1
        nombre = sorted(map(sorted, d.p[k]["ids"]))[0]
        log.append((mov, nombre, d.p[k]["sec"]["nombre"] if d.p[k]["sec"] else None))
        if it % 5 == 0:
            print(f"  paso {it}: {masa0:.1f} kg  K {res['K_tors']:,.0f}  FS5 {res['fs']['LC5']:.2f}", flush=True)
        for mk2 in ((k, "bajar"), (k, "quitar")):
            if mk2 in movimientos(d) or (d.p[k]["sec"] is not None and mk2[1] == "bajar" and piso_idx(d.p[k])[1] < next(j for j, s in enumerate(piso_idx(d.p[k])[0]) if s["nombre"] == d.p[k]["sec"]["nombre"])):
                s2 = puntaje(mk2)
                if s2:
                    heapq.heappush(heap, (-s2[0], cuenta, mk2)); cuenta += 1
    return it


def construir():
    d = Diseno()
    base = base_miembros()
    ex = [(a, b) for a, b, s, t, g in base]
    for a, b, s, tag, gid in base:
        c = clase(a, b, tag, s)
        # lo que se puede podar del vigente: sólo diagonales de torsión
        d.agregar(a, b, s, c, removible=(tag == "tors" or mid((a, b)) in DIAG_ARCO), tag=tag, grupo=gid)
    for a, b in candidatos(ex):
        if mid((a, b)) in PROHIBIDOS or espejo((a, b)) in PROHIBIDOS:
            continue
        d.agregar(a, b, sec_por_nombre("PTR 32x32x1.9"), "otro", True, "tors")
    # partida SOBRADA y factible: todo en la sección más grande de su familia (luego se recorta)
    for v in d.p.values():
        if v["sec"] is not None:
            v["sec"] = (CAT_RED if v["clase"] == "cell" else CAT_PTR)[-1]
    for k, v in d.p.items():
        viol = [m for m in v["ids"] if bloquea(NODES[tuple(m)[0]], NODES[tuple(m)[1]])]
        if viol and v["removible"] and v["tag"] != "tors":
            v["sec"] = None
            print("  quitado de partida (viola un volumen prohibido):", sorted(map(sorted, v["ids"])))
        elif viol and not v["removible"]:
            print("  AVISO: miembro fijo dentro de un volumen prohibido:", sorted(map(sorted, v["ids"])))
    return d


def valencias(d):
    deg = {}
    for a, b, s_, t in d.miembros():
        deg.setdefault(a, []).append(b); deg.setdefault(b, []).append(a)
    return deg


def reducir_valencia(d, max_deg=5):
    """Ningún nodo con más de max_deg tubos: quita (si todo sigue cumpliendo) el removible más pegado a otro."""
    for _ in range(40):
        deg = valencias(d)
        malos = [n for n, v in deg.items() if len(v) > max_deg]
        if not malos:
            return True
        n = malos[0]
        opciones = []
        for k, v in d.p.items():
            if v["sec"] is None or not v["removible"]:
                continue
            if any(n in m for m in v["ids"]):
                dirs = [(_dir(n, next(iter(set(m) - {n})))) for m in v["ids"] if n in m]
                otros = [_dir(n, o) for o in deg[n]]
                ang = min((np.degrees(np.arccos(np.clip(np.dot(dd, oo), -0.999999, 0.999999)))
                           for dd in dirs for oo in otros if abs(np.dot(dd, oo)) < 0.999999), default=90)
                opciones.append((ang, k))
        hecho = False
        for ang, k in sorted(opciones, key=lambda x: x[0]):
            p = aplicar(d, k, "quitar")
            if conectado(p) and cumple(evaluar(p)):
                d.p[k] = p.p[k]; hecho = True
                print(f"  valencia: quitado {sorted(map(sorted, d.p[k]['ids']))} (nodo {n} tenía {len(deg[n])})")
                break
        if not hecho:
            print(f"  AVISO: nodo {n} se queda con {len(deg[n])} tubos")
            return False
    return False


def cruces(miembros, paso=12):
    """Pares de tubos que se tocan en el espacio sin compartir nodo (el constructor los soldaría)."""
    seg = []
    for a, b, s_, t in miembros:
        P = NODES[a][None, :] + (NODES[b] - NODES[a])[None, :] * np.linspace(0, 1, paso)[:, None]
        seg.append((a, b, P, s_["c"]))
    out = []
    for i in range(len(seg)):
        for j in range(i + 1, len(seg)):
            a1, b1, P1, r1 = seg[i]; a2, b2, P2, r2 = seg[j]
            if {a1, b1} & {a2, b2}:
                continue
            dmin = np.min(np.linalg.norm(P1[:, None, :] - P2[None, :, :], axis=2))
            if dmin < r1 + r2:
                out.append((f"{a1}-{b1}", f"{a2}-{b2}", dmin * 1000))
    return out


def partir_cruces(miembros, paso=40):
    """Dos tubos que se tocan en el espacio sin nodo se SUELDAN en la realidad: aquí se inserta un nodo en
    el punto medio de su mínima distancia y los dos tubos se parten ahí (auditoría 2026-10-12)."""
    nuevos = {}
    ms = [list(m) for m in miembros]
    for _ in range(20):
        hallado = None
        for i in range(len(ms)):
            a1, b1, s1, t1 = ms[i]
            P1 = NODES[a1][None, :] + (NODES[b1] - NODES[a1])[None, :] * np.linspace(0, 1, paso)[:, None]
            for j in range(i + 1, len(ms)):
                a2, b2, s2, t2 = ms[j]
                if {a1, b1} & {a2, b2}:
                    continue
                P2 = NODES[a2][None, :] + (NODES[b2] - NODES[a2])[None, :] * np.linspace(0, 1, paso)[:, None]
                D = np.linalg.norm(P1[:, None, :] - P2[None, :, :], axis=2)
                k1, k2 = np.unravel_index(np.argmin(D), D.shape)
                if D[k1, k2] < s1["c"] + s2["c"] and 0 < k1 < paso - 1 and 0 < k2 < paso - 1:
                    hallado = (i, j, (P1[k1] + P2[k2]) / 2)
                    break
            if hallado:
                break
        if not hallado:
            break
        i, j, p = hallado
        nombre = f"x{len(nuevos) + 1}"
        F.registrar_nodo(nombre, p)
        nuevos[nombre] = [float(v) for v in p]
        a1, b1, s1, t1 = ms[i]; a2, b2, s2, t2 = ms[j]
        ms[i] = [a1, nombre, s1, t1]; ms[j] = [a2, nombre, s2, t2]
        ms.append([nombre, b1, s1, t1]); ms.append([nombre, b2, s2, t2])
        print(f"  cruce soldado: {a1}-{b1} x {a2}-{b2} -> nodo {nombre} {np.round(p, 3).tolist()}")
    return [tuple(m) for m in ms], nuevos


def un_intento():
    d = construir()
    r0 = evaluar(d)
    print(f"partida: {len(d.miembros())} miembros, {r0['masa']:.1f} kg, K {r0['K_tors']:,.0f}, cumple={cumple(r0)}")
    log = []
    print("optimización por barrera...", flush=True)
    optimizar_barrera(d, log)
    for ronda in range(1, 4):
        c1 = podar(d, log)
        c2 = dimensionar(d, log)
        r = evaluar(d)
        print(f"ronda {ronda}: {len(d.miembros())} miembros  {r['masa']:.1f} kg  K {r['K_tors']:,.0f}  "
              f"FS {[round(float(r['fs'][c]), 2) for c in ('LC1', 'LC3', 'LC4', 'LC5', 'LC7')]}", flush=True)
        if not (c1 or c2):
            break
    ok = reducir_valencia(d)
    dimensionar(d, log)
    return d, ok


def cruces_ids(miembros, paso=40):
    """Como cruces(), pero devuelve los pares de ids (frozenset de nodos) que se cruzan."""
    out = []
    for a1, b1, a2, b2 in ((x[0], x[1], y[0], y[1]) for i, x in enumerate(miembros) for y in miembros[i + 1:]):
        if {a1, b1} & {a2, b2}:
            continue
        P1 = NODES[a1][None, :] + (NODES[b1] - NODES[a1])[None, :] * np.linspace(0, 1, paso)[:, None]
        P2 = NODES[a2][None, :] + (NODES[b2] - NODES[a2])[None, :] * np.linspace(0, 1, paso)[:, None]
        r = next(m[2]["c"] for m in miembros if {m[0], m[1]} == {a1, b1}) + next(m[2]["c"] for m in miembros if {m[0], m[1]} == {a2, b2})
        if np.min(np.linalg.norm(P1[:, None, :] - P2[None, :, :], axis=2)) < r:
            out.append((frozenset((a1, b1)), frozenset((a2, b2))))
    return out


def main():
    global PROHIBIDOS
    for intento in range(1, 9):
        d, ok = un_intento()
        if ok:
            # ¿se cruzan dos tubos? se veta el candidato (removible) menos cargado del cruce y se re-optimiza
            cr = cruces_ids(d.miembros())
            if cr:
                r = evaluar(d)
                pid_de = {frozenset(m): k for k, v in d.p.items() if v["sec"] is not None for m in v["ids"]}
                opc = []
                for i1, i2 in cr:
                    for i in (i1, i2):
                        k = pid_de.get(i)
                        if k is not None and d.p[k]["removible"] and d.p[k]["tag"] == "tors":
                            nom = tuple(sorted(i))
                            fs = min(r["fs_miembro"].get(nom, 1e9), r["fs_miembro"].get(nom[::-1], 1e9))
                            opc.append((fs, k))
                if opc:
                    _, k = max(opc, key=lambda x: x[0])
                    PROHIBIDOS |= set(d.p[k]["ids"])
                    print(f"  intento {intento}: cruce {[(sorted(a), sorted(b)) for a, b in cr[:2]]} -> se veta {sorted(map(sorted, d.p[k]['ids']))}")
                    continue
            break
        # un nodo quedó con > 5 tubos: se veta el tubo removible MENOS cargado de ese nodo y se re-optimiza
        deg = valencias(d)
        r = evaluar(d)
        n = next(n for n, v in deg.items() if len(v) > 5)
        opciones = [(min(r["fs_miembro"].get(tuple(sorted(m, key=lambda x: x)), 1e9),
                         r["fs_miembro"].get(tuple(m), 1e9), r["fs_miembro"].get(tuple(reversed(tuple(m))), 1e9)), k)
                    for k, v in d.p.items() if v["sec"] is not None and v["removible"] and v["tag"] == "tors"
                    for m in v["ids"] if n in m]
        if not opciones:
            print(f"  nodo {n} saturado y sin tubos vetables: se acepta"); break
        _, k = max(opciones, key=lambda x: x[0])
        PROHIBIDOS |= set(d.p[k]["ids"])
        print(f"  intento {intento}: nodo {n} saturado -> se veta {sorted(map(sorted, d.p[k]['ids']))}")
    mem, extra = partir_cruces(d.miembros())
    cr = cruces(mem)
    print("cruces sin nodo:", cr if cr else "ninguno")
    r = F.evaluar(mem)
    print(f"final: {len(mem)} miembros {r['masa']:.1f} kg K {r['K_tors']:,.0f} "
          f"FS {[round(float(r['fs'][c]), 2) for c in ('LC1', 'LC3', 'LC4', 'LC5', 'LC5c', 'LC6', 'LC7')]}")
    out = dict(nodos_nuevos={**{k: list(v) for k, v in NUEVOS.items()}, **extra},
               masas_mover=MASAS_MOVER, nodos_movidos={k: list(v) for k, v in MOVIDOS.items()},
               miembros=[[a, b, s["nombre"], t] for a, b, s, t in mem],
               resumen=dict(masa=r["masa"], K_tors=r["K_tors"], fs={k: float(v) for k, v in r["fs"].items()}))
    json.dump(out, open(OUT_JSON, "w", encoding="utf-8"), indent=1)
    print("OK", OUT_JSON)
    return d, r


if __name__ == "__main__":
    main()
