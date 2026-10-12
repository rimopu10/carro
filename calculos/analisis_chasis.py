# -*- coding: utf-8 -*-
"""
Análisis estructural del chasis tubular (space frame) — carro eléctrico 2 plazas.

Método: rigidez directa con elementos viga 3D de 12 GDL (axial + flexión 2 ejes +
torsión), uniones soldadas rígidas, análisis estático lineal.

Casos de carga:
  LC1  Bache 3g          — todas las masas ×3 vertical (carga de diseño camino malo)
  LC2  Torsión 1500 N·m  — rigidez torsional del chasis (métrica clave de un deportivo)
  LC3  Frenada 1g        — inercia longitudinal + peso
  LC4  Curva lateral 1g  — inercia lateral + peso

Salidas:
  calculos/resultados-analisis.md   informe con esfuerzos y factores de seguridad
  planos/lista-corte-tubos.csv      lista de corte de cada tubo (longitudes reales)

Limitaciones declaradas: análisis lineal estático; no modela abolladura local del
tubo ni fatiga de soldaduras; el pandeo se verifica por Euler (K=1, conservador).
Validar el diseño final con FEM comercial o FreeCAD antes de soldar.
"""
import numpy as np
import csv, os

# ---------------- materiales y secciones ----------------
E  = 200e9      # Pa, acero
G  = 77e9       # Pa
FY = 250e6      # Pa, fluencia acero estructural comercial (A36/PTR)
RHO = 7850      # kg/m3

# PTR cuadrado 38x38x1.9 mm (calibre 14)
def sec_ptr(b=0.038, t=0.0019):
    bi = b - 2*t
    A  = b*b - bi*bi
    I  = (b**4 - bi**4) / 12.0
    bm = b - t                      # línea media
    J  = 4 * (bm*bm)**2 * t / (4*bm)   # Bredt, pared delgada cerrada
    c  = b/2
    return dict(A=A, Iy=I, Iz=I, J=J, c=c,
                nombre=f"PTR {b*1000:.0f}x{b*1000:.0f}x{t*1000:.1f}")

# Tubo redondo 44.5 x 2.1 mm (1-3/4" cal 14) — arcos de seguridad
def sec_red(do=0.0445, t=0.0032):
    # Pared 3.2 mm, no 2.1: con 2.1 el chasis no pasa el caso de volcadura (LC5) y
    # además 2.1 está en el límite bajo de lo que se acepta para un arco principal.
    di = do - 2*t
    A  = np.pi/4*(do**2 - di**2)
    I  = np.pi/64*(do**4 - di**4)
    J  = 2*I
    c  = do/2
    return dict(A=A, Iy=I, Iz=I, J=J, c=c, nombre=f"RED {do*1000:.1f}x{t*1000:.1f}")

PTR, RED = sec_ptr(), sec_red()
# Diagonales de torsión: PTR 25×25×1.5 en vez de 38×38×1.9. Sale de
# optimizar_chasis.py — quita 9.5 kg (90.5 → 81.0) agregando UN solo tubo a la lista
# de compra, y la rigidez torsional apenas baja de 10,868 a 10,032 N·m/°.
PTR_DIAG = sec_ptr(0.025, 0.0015)
# GAVIOTA (2026-08-16). Al llevar los rieles del techo al espinazo, la cabecera del
# parabrisas y la corona del arco dejan de recibir la carga en el eje y pasan a
# trabajar a FLEXIÓN. Con RED 44.5 el caso de volcadura cae de 1.44 a 1.14; con
# RED 57.2 sube a 1.61. Los tirantes traseros suben con ellos porque, apenas se
# arregla el techo, el tubo crítico se muda a ellos.
RED_CELDA = sec_red(0.0572, 0.0032)
PTR_TRANS = sec_ptr(0.038, 0.0030)   # fx_hi–dash_hi: cierra el bache 3g en 2.06
SEC_POR_TAG = {"tors": PTR_DIAG}

# ---------------- geometría: nodos (x adelante→atrás, y arriba, z lateral) ----------------
NODES = {}
def N(name, x, y, z):
    NODES[name] = np.array([x, y, z])

def mirror(name):
    return name.replace("L", "R") if name.endswith("L") else name.replace("R", "L")

def NM(name, x, y, z):
    """crea nodo lado izquierdo (z+) y su espejo (z-)"""
    N(name + "L", x, y, +z)
    N(name + "R", x, y, -z)

NM("nose",  0.10, 0.30, 0.28)
NM("fb_lo", 0.35, 0.20, 0.50)   # bulkhead frontal inferior (anclaje susp.)
NM("fb_hi", 0.35, 0.48, 0.50)   # bulkhead frontal superior (anclaje susp.)
NM("fx_lo", 0.75, 0.20, 0.55)   # caja frontal trasera inferior
NM("fx_hi", 0.75, 0.48, 0.55)   # caja frontal trasera superior (torre coilover del.)
NM("dash_lo", 1.10, 0.16, 0.58)
# Pie del pilar A adelantado y cabecera atrasada: el parabrisas pasa de 44° a 65° de
# la vertical (44° es ángulo de camioneta). No cuesta acero y el pilar más largo y
# tumbado triangula mejor: la rigidez torsional sube de 12,496 a 13,830 N·m/°.
# 2026-10-11: la piel de Tripo (cofre/pilar A) queda 27 mm más baja que la v3 en el cowl:
# el pie del pilar A baja de 0.72 a 0.65 y la cabecera 20 mm y 20 mm hacia dentro, para
# dejar >= 14 mm de aire bajo el cascarón de 12 mm (calculos/arreglar_chasis_tripo.py).
# K_torsional sube 13,830 -> 14,177 y volcadura 1.61 -> 1.64.
NM("dash_hi", 0.95, 0.65, 0.48)
# Techo 70 mm más abajo (butacas recinadas 12°, escenario D). Baja el arco → palanca
# más corta → el caso de volcadura MEJORA de 1.49 a 1.59.
NM("hdr",   1.45, 0.94, 0.40)   # cabecera parabrisas (esquina del pilar A)
NM("sp_f",  1.45, 0.965, 0.15)   # espinazo delantero — eje de bisagra de la gaviota
NM("sp_r",  2.02, 1.01, 0.15)   # espinazo trasero
NM("seat",  1.62, 0.16, 0.591)  # punto de asiento sobre estribo
NM("mh_lo", 2.02, 0.16, 0.60)   # arco principal pie
NM("mh_belt",2.02, 0.660, 0.506) # barra de cinturones (sobre la pierna del arco). 2026-10-12: 0.742 -> 0.660 = altura real del hombro (maniquí de 1.75 m, buck_piloto.py)
NM("mh_hi", 2.02, 1.01, 0.44)   # arco principal corona
NM("bat_f", 2.10, 0.16, 0.585)  # cuna batería frente (sobre riel)
NM("ta",    2.28, 0.16, 0.552)  # pivote brazo trasero (sobre riel)
NM("bat_r", 2.64, 0.16, 0.486)  # cuna batería atrás (sobre riel)
NM("coil",  2.58, 0.712, 0.425) # torre coilover trasera (sobre riel sup.)
NM("r_lo",  2.78, 0.16, 0.46)
NM("r_hi",  2.78, 0.58, 0.42)
NM("tail",  3.00, 0.35, 0.30)

MEMBERS = []  # (nodoA, nodoB, seccion, etiqueta)
def M(a, b, sec=None, tag="gen"):
    """Si no se da sección explícita, la decide la función del tubo (SEC_POR_TAG)."""
    MEMBERS.append((a, b, sec or SEC_POR_TAG.get(tag, PTR), tag))

def MM(a, b, sec=None, tag="gen"):
    """miembro en ambos lados"""
    M(a + "L", b + "L", sec, tag)
    M(a + "R", b + "R", sec, tag)

def CROSS(a, sec=None, tag="gen"):
    """travesaño entre lados"""
    M(a + "L", a + "R", sec, tag)

# nariz / crush
MM("nose", "fb_lo"); MM("nose", "fb_hi"); CROSS("nose")
# caja frontal (suspensión delantera)
MM("fb_lo", "fb_hi", tag="susp"); MM("fx_lo", "fx_hi", tag="susp")
MM("fb_lo", "fx_lo", tag="susp"); MM("fb_hi", "fx_hi", tag="susp")
MM("fb_hi", "fx_lo", tag="tors")
CROSS("fb_lo"); CROSS("fb_hi"); CROSS("fx_hi")
M("fx_hiL", "fb_hiR", None, "tors")  # X superior
# transición
MM("fx_lo", "dash_lo"); MM("fx_hi", "dash_hi", PTR_TRANS, "safe")
MM("dash_lo", "dash_hi", tag="safe")
CROSS("dash_lo")
# célula: pilares A, techo, estribos, diagonal puerta
MM("dash_hi", "hdr", RED, "safe")
# La cabecera del parabrisas y la corona del arco van PARTIDAS por el espinazo: el
# hueco de la puerta de gaviota se come el techo hasta z=±0.15, así que los rieles
# ya no pueden ir por la orilla — irían dentro del hueco y la puerta les pegaría.
M("hdrL", "sp_fL", RED_CELDA, "safe"); M("sp_fL", "sp_fR", RED_CELDA, "safe")
M("sp_fR", "hdrR", RED_CELDA, "safe")
MM("sp_f", "sp_r", RED_CELDA, "safe")   # rieles de techo = viga de bisagra
MM("dash_lo", "seat", tag="gen"); MM("seat", "mh_lo", tag="gen")   # estribo en 2 tramos
MM("dash_hi", "mh_lo", tag="tors")                                  # diagonal de puerta
M("dash_loL", "mh_loR", None, "tors"); M("dash_loR", "mh_loL", None, "tors")  # X piso
# arco principal (2 tramos por la barra de cinturones)
MM("mh_lo", "mh_belt", RED, "safe"); MM("mh_belt", "mh_hi", RED, "safe")
M("mh_hiL", "sp_rL", RED_CELDA, "safe"); M("sp_rL", "sp_rR", RED_CELDA, "safe")
M("sp_rR", "mh_hiR", RED_CELDA, "safe")
CROSS("mh_belt", PTR, "safe")
M("mh_loL", "mh_hiR", RED, "safe")   # diagonal del arco
# bahía trasera (rieles partidos por cuna/pivote/torre)
MM("mh_lo", "bat_f"); MM("bat_f", "ta"); MM("ta", "bat_r"); MM("bat_r", "r_lo")
# Tirantes traseros del arco principal: son los que bajan la carga de volcadura a la
# estructura trasera. Van en redondo de la célula, no en PTR — sin ellos el FS de LC5
# se queda en 1.10 y el tubo crítico es justamente éste.
MM("mh_hi", "coil", RED_CELDA, "safe"); MM("coil", "r_hi", RED_CELDA, "safe")
MM("r_lo", "r_hi", tag="susp")
MM("mh_lo", "r_hi", tag="tors")
MM("r_lo", "tail"); MM("r_hi", "tail"); CROSS("tail"); CROSS("r_hi"); CROSS("r_lo")
# cuna batería
CROSS("bat_f", tag="batt"); CROSS("bat_r", tag="batt")
MM("bat_f", "bat_r", tag="batt")

# ---------------- REDISEÑO 2026-10-11 (calculos/rediseno_chasis.py) ----------------
# Si existe calculos/chasis_rediseno.json, ESE es el chasis: mismos nodos duros, hueco de puerta
# libre (se quitó la diagonal dash_hi-mh_lo que cruzaba la entrada), tubos recolocados por
# optimización de estructura y secciones bajadas donde sobraban. Borrar el JSON devuelve el
# diseño anterior de arriba.
_RED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chasis_rediseno.json")
if os.path.exists(_RED) and not os.environ.get("CHASIS_BASE"):   # CHASIS_BASE=1: el diseño de partida
    import json as _json, re as _re
    _d = _json.load(open(_RED, encoding="utf-8"))
    def _sec(nombre):
        t, dims = nombre.split(" ", 1)
        v = [float(x) for x in dims.split("x")]
        return sec_ptr(v[0]/1000, v[2]/1000) if t == "PTR" else sec_red(v[0]/1000, v[1]/1000)
    for _n, _p in _d["nodos_nuevos"].items():
        N(_n, *_p)
    MEMBERS[:] = [(a, b, _sec(sn), tag) for a, b, sn, tag in _d["miembros"]]
    _usados = {n for m in MEMBERS for n in m[:2]}
    for _n in [n for n in NODES if n not in _usados]:      # nodo nuevo que la optimización dejó sin tubos
        print(f"  (nodo {_n} sin tubos: se descarta)")
        del NODES[_n]
    for _n, _p in _d.get("nodos_movidos", {}).items():      # nodos del diseño base que el rediseño reubica
        N(_n, *_p)
    _MOVER = _d.get("masas_mover", {})
else:
    _MOVER = {}

# ---------------- ensamble FEM viga 3D ----------------
names = sorted(NODES)
idx = {n: i for i, n in enumerate(names)}
ndof = 6 * len(names)

def beam_k_local(Le, s):
    A_, Iy, Iz, J = s["A"], s["Iy"], s["Iz"], s["J"]
    L2, L3 = Le*Le, Le**3
    k = np.zeros((12, 12))
    ax, tr = E*A_/Le, G*J/Le
    by, bz = E*Iz, E*Iy
    k[0,0]=k[6,6]=ax;  k[0,6]=k[6,0]=-ax
    k[3,3]=k[9,9]=tr;  k[3,9]=k[9,3]=-tr
    for (i1,i2,i3,i4,B) in [(1,5,7,11,by),(2,4,8,10,bz)]:
        sgn = 1.0 if i1==1 else -1.0
        k[i1,i1]=k[i3,i3]= 12*B/L3;  k[i1,i3]=k[i3,i1]=-12*B/L3
        k[i2,i2]=k[i4,i4]= 4*B/Le;   k[i2,i4]=k[i4,i2]= 2*B/Le
        k[i1,i2]=k[i2,i1]= sgn*6*B/L2;  k[i1,i4]=k[i4,i1]= sgn*6*B/L2
        k[i3,i2]=k[i2,i3]=-sgn*6*B/L2;  k[i3,i4]=k[i4,i3]=-sgn*6*B/L2
    return k

def transform(a, b):
    v = b - a; Le = np.linalg.norm(v); ex = v/Le
    ref = np.array([0,0,1.0]) if abs(ex[2]) < 0.95 else np.array([1.0,0,0])
    ez = np.cross(ex, ref); ez /= np.linalg.norm(ez)
    ey = np.cross(ez, ex)
    R = np.vstack([ex, ey, ez])
    T = np.zeros((12,12))
    for q in range(4):
        T[3*q:3*q+3, 3*q:3*q+3] = R
    return T, Le

K = np.zeros((ndof, ndof))
elems = []
for (a, b, s, tag) in MEMBERS:
    pa, pb = NODES[a], NODES[b]
    T, Le = transform(pa, pb)
    kl = beam_k_local(Le, s)
    kg = T.T @ kl @ T
    dof = np.r_[6*idx[a]:6*idx[a]+6, 6*idx[b]:6*idx[b]+6]
    K[np.ix_(dof, dof)] += kg
    elems.append(dict(a=a, b=b, sec=s, tag=tag, T=T, kl=kl, dof=dof, L=Le))

masa_acero = sum(e["L"]*e["sec"]["A"]*RHO for e in elems)

# ---------------- masas y cargas ----------------
g = 9.81
MASAS = {  # kg aplicados en nodos (por nodo)
    "bat_fL": 22.5, "bat_fR": 22.5, "bat_rL": 22.5, "bat_rR": 22.5,   # batería 90 kg
    "seatL": 90.0, "seatR": 90.0,                                       # 2 ocupantes
    "noseL": 7.5, "noseR": 7.5,                                         # controladores/cargador
    "dash_loL": 10, "dash_loR": 10, "mh_loL": 10, "mh_loR": 10,         # carrocería ~40 kg en anclajes
}

# CORREGIDO 2026-08-05. Lo de arriba suma 325 kg, pero la masa SUSPENDIDA real del
# carro es 690 − 126 de masa no suspendida (2×18 delante + 2×45 atrás, los motores de
# cubo) = 564 kg. Faltaban 239 kg, incluido el propio chasis, que nadie aplicaba: el
# FEM estaba verificando la estructura con el 58% de su carga. Se reparte el faltante
# entre los nodos en proporción al tubo que llega a cada uno — que es exactamente cómo
# se distribuye el peso propio del frame y lo que va atornillado a él.
MASA_TOTAL_CARRO = 690.0
MASA_NO_SUSPENDIDA = 2 * 18.0 + 2 * 45.0
MASA_SUSPENDIDA = MASA_TOTAL_CARRO - MASA_NO_SUSPENDIDA
for _o, _t in _MOVER.items():       # el ocupante pesa donde se atornillan los rieles de su asiento
    _m = MASAS.pop(_o)
    for _n, _f in (_t.items() if isinstance(_t, dict) else [(_t, 1.0)]):
        MASAS[_n] = MASAS.get(_n, 0.0) + _m * _f
_falta = MASA_SUSPENDIDA - sum(MASAS.values())
if _falta > 0:
    _tubo_por_nodo = {n: 0.0 for n in NODES}
    for (a, b, s, tag) in MEMBERS:
        L = float(np.linalg.norm(NODES[b] - NODES[a]))
        _tubo_por_nodo[a] += L / 2
        _tubo_por_nodo[b] += L / 2
    _tot = sum(_tubo_por_nodo.values())
    for n, L in _tubo_por_nodo.items():
        MASAS[n] = MASAS.get(n, 0.0) + _falta * L / _tot

def F_vector(ax_g=0.0, ay_g=-1.0, az_g=0.0):
    """vector de fuerzas por inercia: aceleración en g's por eje"""
    F = np.zeros(ndof)
    for n, m in MASAS.items():
        i = 6*idx[n]
        F[i+0] += m*g*ax_g
        F[i+1] += m*g*ay_g
        F[i+2] += m*g*az_g
    return F

def solve(F, fixed_dofs):
    free = np.setdiff1d(np.arange(ndof), fixed_dofs)
    U = np.zeros(ndof)
    U[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
    return U

def fix(node, comps):
    return [6*idx[node] + c for c in comps]

# apoyos normales: verticales en torres coilover, horizontales en pivotes
SUP = (fix("fx_hiL", [1]) + fix("fx_hiR", [1]) + fix("coilL", [1]) + fix("coilR", [1])
       + fix("fb_loL", [0, 2]) + fix("fb_loR", [2]) + fix("taL", [2]))

def esfuerzo_max(e, U):
    ul = e["T"] @ U[e["dof"]]
    fl = e["kl"] @ ul
    s = e["sec"]
    Nax = abs(fl[0])
    sig = 0.0
    for end in (0, 1):
        My = abs(fl[4 + 6*end]); Mz = abs(fl[5 + 6*end])
        sb = My*s["c"]/s["Iy"] + Mz*s["c"]/s["Iz"]
        sig = max(sig, Nax/s["A"] + sb)
    # pandeo Euler si compresión (fl[0] > 0 = compresión en convención local aquí: revisar signo)
    Ncomp = fl[0] if fl[0] > 0 else fl[6] if fl[6] > 0 else 0.0
    Pcr = np.pi**2 * E * min(s["Iy"], s["Iz"]) / e["L"]**2
    fs_buck = Pcr/Ncomp if Ncomp > 1.0 else np.inf
    return sig, fs_buck

def analizar(nombre, F, sup=SUP):
    U = solve(F, sup)
    filas = []
    for e in elems:
        sig, fsb = esfuerzo_max(e, U)
        fs = FY/sig if sig > 0 else np.inf
        filas.append((f'{e["a"]}-{e["b"]}', e["tag"], e["sec"]["nombre"], sig/1e6, fs, fsb))
    filas.sort(key=lambda r: r[4])
    return U, filas

def F_vuelco(nv, nl):
    """LC5 VOLCADURA. El FEM no tenía caso de volcadura, que es justo el trabajo del
    arco principal. Se aplica en la corona del arco (`mh_hi`) una carga proporcional al
    peso del carro: nv veces W en vertical hacia abajo y nl veces W lateral, que es el
    criterio de club para un vehículo de menos de 900 kg. La FIA pide 7.5W/1.5W/5.5W
    para un arco homologado; aquí se reporta el FS con ambos."""
    W = MASA_TOTAL_CARRO * g
    F = np.zeros(ndof)
    for n, s in [("mh_hiL", 1.0), ("mh_hiR", 1.0)]:
        i = 6 * idx[n]
        F[i + 1] -= nv * W / 2
        F[i + 2] += nl * W / 2
    return F

resultados = {}
resultados["LC1 Bache 3g"]   = analizar("LC1", F_vector(0, -3.0, 0))
resultados["LC5 Volcadura (2.0W vert + 0.75W lat)"] = analizar("LC5", F_vuelco(2.0, 0.75))
resultados["LC5b Volcadura FIA (7.5W + 5.5W)"] = analizar("LC5b", F_vuelco(7.5, 5.5))
def F_vuelco_cabecera(nv, nl):
    """LC5c: la volcadura también carga la cabecera del parabrisas (esquinas hdr), no sólo el arco."""
    W = MASA_TOTAL_CARRO * g
    F = np.zeros(ndof)
    for n in ("hdrL", "hdrR"):
        i = 6 * idx[n]
        F[i + 1] -= nv * W / 2
        F[i + 2] += nl * W / 2
    return F

resultados["LC5c Volcadura sobre la cabecera (1.0W vert + 0.5W lat)"] = analizar("LC5c", F_vuelco_cabecera(1.0, 0.5))
if "h1L" in NODES:     # el rediseño trae bisagras y amortiguador: LC7 puertas abiertas a 65 grados
    import puertas as _PU
    _F7 = np.zeros(ndof)
    for _n, _f in _PU.lc7().items():
        _F7[6*idx[_n]:6*idx[_n]+6] += _f
    resultados["LC7 Puertas abiertas a 65° (3g + viento 400 N + amortiguador)"] = analizar("LC7", _F7)
resultados["LC3 Frenada 1g"] = analizar("LC3", F_vector(-1.0, -1.0, 0))
resultados["LC4 Curva 1g"]   = analizar("LC4", F_vector(0, -1.0, 1.0))

# LC2: rigidez torsional — par en el eje delantero, trasero fijo
SUP_T = (fix("coilL", [0,1,2]) + fix("coilR", [0,1,2]) + fix("taL", [0,1,2]) + fix("taR", [0,1,2]))
Fq = np.zeros(ndof)
Par = 1500.0  # N·m
brazo = abs(NODES["fx_hiL"][2])
Fq[6*idx["fx_hiL"] + 1] = +Par/(2*brazo)
Fq[6*idx["fx_hiR"] + 1] = -Par/(2*brazo)
Ut = solve(Fq, SUP_T)
dyL = Ut[6*idx["fx_hiL"] + 1]; dyR = Ut[6*idx["fx_hiR"] + 1]
theta = (dyL - dyR)/(2*brazo)
K_tors = Par/np.degrees(theta)  # N·m/grado

# LC6: resistencia a la torsión de un bache en UNA rueda a 3g ~ 3x el par de la prueba de rigidez
Fq6 = 3.0 * Fq
U6 = solve(Fq6, SUP_T)
FS_TORS6 = min((FY / max(esfuerzo_max(e, U6)[0], 1.0)) for e in elems)

# ---------------- informes ----------------
os.makedirs(os.path.join(os.path.dirname(__file__), "..", "planos"), exist_ok=True)
out_md = os.path.join(os.path.dirname(__file__), "resultados-analisis.md")
with open(out_md, "w", encoding="utf-8") as f:
    f.write("# Resultados del análisis estructural del chasis\n\n")
    f.write("Método: rigidez directa, vigas 3D 12-GDL, uniones rígidas, estático lineal.\n")
    f.write(f"Acero fy=250 MPa · E=200 GPa · PTR 38×38×1.9 y arcos RED 44.5×2.1.\n\n")
    f.write(f"**Miembros:** {len(elems)} tubos · **masa del chasis:** {masa_acero:.1f} kg · ")
    f.write(f"**longitud total de tubo:** {sum(e['L'] for e in elems):.1f} m\n\n")
    f.write(f"## Rigidez torsional\n\n**{K_tors:,.0f} N·m/°** con par de {Par:.0f} N·m ")
    f.write("(objetivo para deportivo ligero artesanal: >4,000 N·m/°; un kit car típico ronda 2,000-6,000).\n\n")
    for lc, (U, filas) in resultados.items():
        fs_min = filas[0][4]
        f.write(f"## {lc}\n\n")
        f.write(f"Factor de seguridad mínimo: **{fs_min:.1f}** (>2.0 requerido, >3.0 deseable)\n\n")
        f.write("Los 10 tubos más esforzados:\n\n")
        f.write("| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |\n|---|---|---|---|---|---|\n")
        for (mm, tag, sec, sig, fs, fsb) in filas[:10]:
            fsb_s = f"{fsb:.1f}" if np.isfinite(fsb) else "—"
            f.write(f"| {mm} | {tag} | {sec} | {sig:.1f} | {fs:.1f} | {fsb_s} |\n")
        f.write("\n")
    f.write("## Supuestos y límites\n\n")
    f.write("- Masas: batería 90 kg, 2 ocupantes 180 kg, controladores 15 kg, carrocería 40 kg en anclajes.\n")
    f.write("- Motores de cubo = masa no suspendida: no cargan el chasis en estos casos.\n")
    f.write("- No incluye: fatiga de soldadura, abolladura local, choque. Validar con FEM 3D antes de soldar.\n")

# lista de corte
out_csv = os.path.join(os.path.dirname(__file__), "..", "planos", "lista-corte-tubos.csv")
with open(out_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    # Lista de corte DE VERDAD: no la distancia entre centros de nodo (que no se puede
    # cortar), sino la longitud real de la pieza más el ángulo de cada extremo.
    # En cada nudo, el tubo se topa contra el más grueso que llega ahí: se descuenta
    # c_vecino/sen(θ) y se corta a inglete θ/2 (o destaje de silla si el vecino es
    # redondo). CORREGIDO 2026-08-05: antes solo salía la longitud entre centros.
    # Nodos VIRTUALES (bases de bisagra h1/h2 y ancla del amortiguador sa): en el FEM parten el tubo para aplicar la
    # carga, pero en el taller son placas soldadas sobre UN tubo continuo -> en la lista de corte se fusionan.
    VIRTUALES = {"h1L", "h2L", "saL", "h1R", "h2R", "saR"}
    def fusionar(lista):
        lista = list(lista)
        for vn in VIRTUALES:
            tocan = [e for e in lista if vn in (e["a"], e["b"])]
            if len(tocan) == 2 and tocan[0]["sec"]["nombre"] == tocan[1]["sec"]["nombre"]:
                e1, e2 = tocan
                o1 = e1["b"] if e1["a"] == vn else e1["a"]
                o2 = e2["b"] if e2["a"] == vn else e2["a"]
                nuevo = dict(e1); nuevo["a"], nuevo["b"], nuevo["L"] = o1, o2, e1["L"] + e2["L"]
                lista = [e for e in lista if e is not e1 and e is not e2] + [nuevo]
        return lista
    elems_corte = fusionar(elems)
    def vecinos(nodo, propio):
        return [o for o in elems_corte if o is not propio and nodo in (o["a"], o["b"])]
    def dirv(e, desde):
        v = NODES[e["b"]] - NODES[e["a"]]
        return v / np.linalg.norm(v) * (1 if e["a"] == desde else -1)
    w.writerow(["#", "de_nodo", "a_nodo", "seccion", "funcion",
                "largo_entre_centros_mm", "largo_de_corte_mm",
                "extremo_A_topa_contra", "angulo_A_grados", "corte_A",
                "extremo_B_topa_contra", "angulo_B_grados", "corte_B",
                "x1", "y1", "z1", "x2", "y2", "z2"])
    for i, e in enumerate(sorted(elems_corte, key=lambda e: (e["sec"]["nombre"], -e["L"])), 1):
        pa, pb = NODES[e["a"]], NODES[e["b"]]
        det, desc = [], 0.0
        for nodo in (e["a"], e["b"]):
            vs = vecinos(nodo, e)
            if not vs:
                det += ["libre", "90", "recto"]
                continue
            mio = dirv(e, nodo)
            # se topa contra el vecino más grueso; si empatan, el más perpendicular
            best = max(vs, key=lambda o: (o["sec"]["c"], abs(float(np.dot(mio, dirv(o, nodo))))))
            dot = float(np.dot(mio, dirv(best, nodo)))
            phi = np.degrees(np.arccos(np.clip(dot, -1, 1)))
            if phi > 150.0:
                # CORREGIDO 2026-10-12 (auditoría): el vecino CONTINÚA en línea recta (o casi).
                # Antes se tomaba abs(dot) -> ángulo 0 -> se subía a 12° -> se descontaban 4.8·c
                # y salían cortes negativos. Un tubo que continúa a tope se corta recto (o a un
                # inglete de (180-phi)/2) y sólo pierde r·tan((180-phi)/2).
                defl = 180.0 - phi
                desc += best["sec"]["c"] * np.tan(np.radians(defl / 2))
                det += [f'{best["a"]}-{best["b"]}', f"{phi:.0f}",
                        "recto" if defl < 2 else f"inglete {defl/2:.0f}°"]
                continue
            th = np.degrees(np.arccos(np.clip(abs(dot), 0, 1)))
            th = max(th, 12.0)
            desc += best["sec"]["c"] / np.sin(np.radians(th))
            redondo = best["sec"]["nombre"].startswith("RED")
            det += [f'{best["a"]}-{best["b"]}', f"{th:.0f}",
                    "destaje de silla" if redondo else f"inglete {th/2:.0f}°"]
        w.writerow([i, e["a"], e["b"], e["sec"]["nombre"], e["tag"],
                    f"{e['L']*1000:.0f}", f"{(e['L']-desc)*1000:.0f}", *det,
                    *[f"{v*1000:.0f}" for v in pa], *[f"{v*1000:.0f}" for v in pb]])

print(f"OK  {len(elems)} miembros | masa chasis {masa_acero:.1f} kg | "
      f"tubo total {sum(e['L'] for e in elems):.1f} m | K_torsional {K_tors:,.0f} N·m/deg")
for lc, (U, filas) in resultados.items():
    print(f"{lc}: FS_min = {filas[0][4]:.2f}  en  {filas[0][0]}")
print(f"LC6 Torsion 4,500 N.m (bache en una rueda a 3g): FS_min = {FS_TORS6:.2f}")
