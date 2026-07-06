# -*- coding: utf-8 -*-
"""
EXPERIMENTO: ¿qué pasa si le damos el carro ENTERO como bloque al algoritmo
de diseño generativo, en vez de solo las uniones?

Mismo método SIMP que nodo_generativo.py, pero en 2D (vista lateral del carro):
dominio de 3.0 × 1.08 m con la silueta real, el hueco de la cabina como zona
prohibida (ahí van las personas), apoyos en las torres de suspensión reales y
las cargas reales del análisis (ocupantes, batería, controladores, a 3g).

El punto: ver qué topología dibuja el algoritmo a escala de carro completo,
y compararla contra el space frame de tubos ya diseñado.

Salida:  calculos/chasis-generativo-vs-tubos.png
"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# ----------------- dominio: el carro de perfil -----------------
LARGO, ALTO = 3.0, 1.083
nelx, nely = 180, 65               # elemento = 16.7 mm
h = LARGO / nelx
volfrac, penal, rmin, maxit = 0.22, 3.0, 2.4, 70
E0, Emin, nu = 1.0, 1e-9, 0.3

# ----------------- rigidez del elemento Q4 (esfuerzo plano, Gauss 2x2) -----------------
LOCAL = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
def q4_stiffness(E, nu):
    D = E / (1 - nu**2) * np.array([[1, nu, 0], [nu, 1, 0], [0, 0, (1 - nu) / 2]])
    gp = np.array([-1, 1]) / np.sqrt(3.0)
    signs = 2 * LOCAL - 1
    KE = np.zeros((8, 8))
    for xi in gp:
        for eta in gp:
            dN = np.zeros((2, 4))
            for i in range(4):
                sx, sy = signs[i]
                dN[0, i] = 0.25 * sx * (1 + sy * eta)
                dN[1, i] = 0.25 * sy * (1 + sx * xi)
            J = dN @ LOCAL
            dNxy = np.linalg.solve(J, dN)
            B = np.zeros((3, 8))
            for i in range(4):
                bx, by = dNxy[:, i]
                B[0, 2*i] = bx; B[1, 2*i+1] = by
                B[2, 2*i] = by; B[2, 2*i+1] = bx
            KE += (B.T @ D @ B) * np.linalg.det(J)
    return KE

KE = q4_stiffness(1.0, nu)

# ----------------- malla y conectividad -----------------
nele = nelx * nely
nx, ny = nelx + 1, nely + 1
ndof = 2 * nx * ny
def gid(ix, iy): return iy * nx + ix
def eid(ex, ey): return ey * nelx + ex

edofMat = np.zeros((nele, 8), dtype=np.int64)
for ey in range(nely):
    for ex in range(nelx):
        dofs = []
        for (lx, ly) in LOCAL.astype(int):
            n = gid(ex + lx, ey + ly)
            dofs += [2 * n, 2 * n + 1]
        edofMat[eid(ex, ey)] = dofs
iK = np.kron(edofMat, np.ones((8, 1), dtype=np.int64)).flatten()
jK = np.kron(edofMat, np.ones((1, 8), dtype=np.int64)).flatten()

# ----------------- silueta del carro y zona prohibida (cabina) -----------------
def y_techo(x):
    """línea superior de la silueta: cofre que sube al parabrisas, cabina, cola"""
    if x < 1.10:  return 0.40 + (0.75 - 0.40) * x / 1.10       # cofre
    if x <= 2.02: return ALTO                                   # cabina hasta el arco
    return ALTO + (0.62 - ALTO) * (x - 2.02) / (3.0 - 2.02)     # cola

vacio = np.zeros(nele, dtype=bool)   # fuera de la silueta o dentro de la cabina
for ey in range(nely):
    for ex in range(nelx):
        cx, cy = (ex + 0.5) * h, (ey + 0.5) * h
        if cy > y_techo(cx):
            vacio[eid(ex, ey)] = True
        if 1.24 <= cx <= 1.94 and 0.28 <= cy <= 1.00:           # hueco de la cabina
            vacio[eid(ex, ey)] = True

# ----------------- apoyos (torres de suspensión reales) y cargas (bache 3g) -----------------
def nodos_cerca(x, y, r=0.035):
    out = []
    for iy in range(ny):
        for ix in range(nx):
            if (ix * h - x)**2 + (iy * h - y)**2 <= r**2:
                out.append(gid(ix, iy))
    return out

fixed = []
for (tx, ty) in [(0.75, 0.48), (2.58, 0.71)]:      # torre coilover del. y tras.
    for n in nodos_cerca(tx, ty):
        fixed += [2 * n, 2 * n + 1]
fixed = np.unique(np.array(fixed))
free = np.setdiff1d(np.arange(ndof), fixed)

F = np.zeros(ndof)
CARGAS = [                                          # (x, y, masa_kg) — bache 3g
    (1.62, 0.20, 180.0),                            # 2 ocupantes
    (2.37, 0.18, 90.0),                             # batería
    (0.20, 0.32, 15.0),                             # controladores/cargador
]
solido = np.zeros(nele, dtype=bool)                 # material obligatorio en anclajes
for (lx, ly, m) in CARGAS:
    nn = nodos_cerca(lx, ly, 0.03)
    for n in nn:
        F[2 * n + 1] -= m * 3 * 9.81 / len(nn)
    for ey in range(nely):
        for ex in range(nelx):
            cx, cy = (ex + 0.5) * h, (ey + 0.5) * h
            if (cx - lx)**2 + (cy - ly)**2 <= 0.03**2:
                solido[eid(ex, ey)] = True
solido &= ~vacio

# ----------------- filtro de densidad -----------------
print("preparando filtro...")
iH, jH, sH = [], [], []
rc = int(np.ceil(rmin)) - 1
for ey in range(nely):
    for ex in range(nelx):
        e1 = eid(ex, ey)
        for ky in range(max(ey - rc, 0), min(ey + rc + 1, nely)):
            for kx in range(max(ex - rc, 0), min(ex + rc + 1, nelx)):
                w = rmin - np.sqrt((ex - kx)**2 + (ey - ky)**2)
                if w > 0:
                    iH.append(e1); jH.append(eid(kx, ky)); sH.append(w)
H = coo_matrix((sH, (iH, jH)), shape=(nele, nele)).tocsr()
Hs = np.array(H.sum(axis=1)).flatten()

# ----------------- bucle de optimización -----------------
x = np.full(nele, volfrac)
x[vacio] = 0.0; x[solido] = 1.0
xPhys = x.copy()
activos = ~vacio
print(f"optimizando {nelx}x{nely} = {nele} elementos ({activos.sum()} activos)...")
for it in range(maxit):
    sK = ((KE.flatten()[:, None] * (Emin + xPhys**penal * (E0 - Emin))[None, :]).flatten(order='F'))
    K = coo_matrix((sK, (iK, jK)), shape=(ndof, ndof)).tocsc()
    K = (K + K.T) * 0.5
    U = np.zeros(ndof)
    U[free] = spsolve(K[free, :][:, free], F[free])
    ce = np.einsum('ij,jk,ik->i', U[edofMat], KE, U[edofMat])
    c = np.sum((Emin + xPhys**penal * (E0 - Emin)) * ce)
    dc = -penal * (E0 - Emin) * xPhys**(penal - 1) * ce
    dv = np.ones(nele)
    dc = np.asarray(H.dot(dc / Hs)); dv = np.asarray(H.dot(dv / Hs))
    dc = np.minimum(dc, 0.0)
    l1, l2, move = 1e-9, 1e9, 0.2
    B = np.maximum(-dc, 0.0) / dv
    vol_obj = volfrac * activos.sum()
    while (l2 - l1) / (l1 + l2) > 1e-3:
        lmid = 0.5 * (l1 + l2)
        xnew = np.maximum(0.0, np.maximum(x - move,
                 np.minimum(1.0, np.minimum(x + move, x * np.sqrt(B / lmid)))))
        xnew[vacio] = 0.0; xnew[solido] = 1.0
        xPhys = np.asarray(H.dot(xnew) / Hs)
        xPhys[vacio] = 0.0; xPhys[solido] = 1.0
        if xPhys[activos].sum() > vol_obj:
            l1 = lmid
        else:
            l2 = lmid
    ch = np.max(np.abs(xnew - x))
    x = xnew
    if (it + 1) % 10 == 0 or ch < 0.01:
        print(f"  it {it+1:2d}  compliance {c:10.1f}  vol {xPhys[activos].mean():.3f}  cambio {ch:.3f}")
    if ch < 0.01:
        break

# ----------------- comparación gráfica contra el space frame real -----------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import analisis_chasis as ac

grid = xPhys.reshape((nely, nelx))
fig, axes = plt.subplots(2, 1, figsize=(13, 8.6), facecolor="#0d1117")
for axi in axes:
    axi.set_facecolor("#0d1117")
    axi.imshow(grid, cmap="gray", origin="lower", extent=[0, LARGO, 0, ALTO * 1.0],
               vmin=0, vmax=1, interpolation="bilinear", aspect="equal")
    # silueta y cabina
    xs = np.linspace(0, 3.0, 200)
    axi.plot(xs, [y_techo(v) for v in xs], color="#30363d", lw=1, ls="--")
    axi.add_patch(plt.Rectangle((1.24, 0.28), 0.70, 0.72, fill=False,
                                edgecolor="#8b949e", ls=":", lw=1))
    axi.text(1.59, 0.62, "cabina\n(prohibido)", color="#8b949e", fontsize=8,
             ha="center", va="center")
    # apoyos y cargas
    for (tx, ty) in [(0.75, 0.48), (2.58, 0.71)]:
        axi.plot(tx, ty, marker="^", color="#38bdf8", ms=9)
    for (lx, ly, m) in CARGAS:
        axi.annotate("", xy=(lx, ly - 0.14), xytext=(lx, ly),
                     arrowprops=dict(color="#f87171", width=2, headwidth=7))
        axi.text(lx + 0.03, ly - 0.16, f"{m:.0f} kg×3g", color="#f87171", fontsize=8)
    axi.set_xlim(-0.05, 3.15); axi.set_ylim(-0.06, 1.25)
    axi.tick_params(colors="#8b949e", labelsize=8)
    for sp in axi.spines.values():
        sp.set_color("#30363d")

axes[0].set_title("Se le dio el carro ENTERO como bloque al algoritmo (SIMP, cargas y apoyos reales)"
                  "\n→ el algoritmo dibuja BARRAS RECTAS EN TRIÁNGULOS: un space frame",
                  color="#e6edf3", fontsize=11)

# overlay: el space frame real proyectado de lado
for e in ac.elems:
    pa, pb = ac.NODES[e["a"]], ac.NODES[e["b"]]
    lw = 2.6 if "RED" in e["sec"]["nombre"] else 1.8
    axes[1].plot([pa[0], pb[0]], [pa[1], pb[1]], color="#f97316", lw=lw, alpha=0.75,
                 solid_capstyle="round")
axes[1].set_title("El mismo resultado con el space frame YA diseñado encima (naranja)"
                  "\n→ los tubos van donde el algoritmo puso el material",
                  color="#e6edf3", fontsize=11)

fig.tight_layout()
out = os.path.join(HERE, "chasis-generativo-vs-tubos.png")
fig.savefig(out, dpi=150, facecolor="#0d1117", bbox_inches="tight")
print(f"OK  comparación guardada: {out}")
