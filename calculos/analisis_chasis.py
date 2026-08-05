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
def sec_red():
    do, t = 0.0445, 0.0021
    di = do - 2*t
    A  = np.pi/4*(do**2 - di**2)
    I  = np.pi/64*(do**4 - di**4)
    J  = 2*I
    c  = do/2
    return dict(A=A, Iy=I, Iz=I, J=J, c=c, nombre="RED 44.5x2.1")

PTR, RED = sec_ptr(), sec_red()
# Diagonales de torsión: PTR 25×25×1.5 en vez de 38×38×1.9. Sale de
# optimizar_chasis.py — quita 9.5 kg (90.5 → 81.0) agregando UN solo tubo a la lista
# de compra, y la rigidez torsional apenas baja de 10,868 a 10,032 N·m/°.
PTR_DIAG = sec_ptr(0.025, 0.0015)
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
NM("dash_hi", 1.10, 0.72, 0.48)
NM("hdr",   1.32, 1.02, 0.42)   # cabecera parabrisas
NM("seat",  1.62, 0.16, 0.591)  # punto de asiento sobre estribo
NM("mh_lo", 2.02, 0.16, 0.60)   # arco principal pie
NM("mh_belt",2.02, 0.78, 0.492) # nodo barra de cinturones (sobre la pierna del arco)
NM("mh_hi", 2.02, 1.08, 0.44)   # arco principal corona
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
MM("fx_lo", "dash_lo"); MM("fx_hi", "dash_hi"); MM("dash_lo", "dash_hi", tag="safe")
CROSS("dash_lo")
# célula: pilares A, techo, estribos, diagonal puerta
MM("dash_hi", "hdr", RED, "safe"); CROSS("hdr", RED, "safe")
MM("hdr", "mh_hi", RED, "safe")
MM("dash_lo", "seat", tag="gen"); MM("seat", "mh_lo", tag="gen")   # estribo en 2 tramos
MM("dash_hi", "mh_lo", tag="tors")                                  # diagonal de puerta
M("dash_loL", "mh_loR", None, "tors"); M("dash_loR", "mh_loL", None, "tors")  # X piso
# arco principal (2 tramos por la barra de cinturones)
MM("mh_lo", "mh_belt", RED, "safe"); MM("mh_belt", "mh_hi", RED, "safe")
CROSS("mh_hi", RED, "safe"); CROSS("mh_belt", PTR, "safe")
M("mh_loL", "mh_hiR", RED, "safe")   # diagonal del arco
# bahía trasera (rieles partidos por cuna/pivote/torre)
MM("mh_lo", "bat_f"); MM("bat_f", "ta"); MM("ta", "bat_r"); MM("bat_r", "r_lo")
MM("mh_hi", "coil", tag="susp"); MM("coil", "r_hi", tag="susp")
MM("r_lo", "r_hi", tag="susp")
MM("mh_lo", "r_hi", tag="tors")
MM("r_lo", "tail"); MM("r_hi", "tail"); CROSS("tail"); CROSS("r_hi"); CROSS("r_lo")
# cuna batería
CROSS("bat_f", tag="batt"); CROSS("bat_r", tag="batt")
MM("bat_f", "bat_r", tag="batt")

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

resultados = {}
resultados["LC1 Bache 3g"]   = analizar("LC1", F_vector(0, -3.0, 0))
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
    w.writerow(["#", "de_nodo", "a_nodo", "seccion", "funcion", "longitud_mm",
                "x1", "y1", "z1", "x2", "y2", "z2"])
    for i, e in enumerate(sorted(elems, key=lambda e: (e["sec"]["nombre"], -e["L"])), 1):
        pa, pb = NODES[e["a"]], NODES[e["b"]]
        w.writerow([i, e["a"], e["b"], e["sec"]["nombre"], e["tag"], f"{e['L']*1000:.0f}",
                    *[f"{v*1000:.0f}" for v in pa], *[f"{v*1000:.0f}" for v in pb]])

print(f"OK  {len(elems)} miembros | masa chasis {masa_acero:.1f} kg | "
      f"tubo total {sum(e['L'] for e in elems):.1f} m | K_torsional {K_tors:,.0f} N·m/deg")
for lc, (U, filas) in resultados.items():
    print(f"{lc}: FS_min = {filas[0][4]:.2f}  en  {filas[0][0]}")
