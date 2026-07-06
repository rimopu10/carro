# -*- coding: utf-8 -*-
"""
DISEÑO GENERATIVO REAL — optimización topológica 3D de un nodo de chasis.

Esto es lo que hace Czinger: en vez de soldar tubos, las UNIONES donde se cruzan
varios tubos se vuelven piezas orgánicas diseñadas por algoritmo, impresas en 3D.
El algoritmo empieza con un bloque de material y le quita todo lo que no trabaja,
dejando una estructura tipo hueso que sigue las líneas de fuerza.

Método: SIMP (Solid Isotropic Material with Penalization) en 3D con elementos
finitos hexaédricos de 8 nodos (24 GDL/elemento), filtro de densidad, actualización
por criterio de optimalidad (OC). Port fiel del algoritmo académico "top3d" de Liu &
Tovar (2014), el estándar de referencia mundial para topología 3D.

Caso: nodo de suspensión delantera. A este punto llegan 5 tubos (bulkhead, caja,
estribo, torre de coilover) y entra la carga de la rueda. El algoritmo esculpe el
nodo que conecta todo con mínimo material.

Salidas:
  cad/nodo-suspension.stl          malla imprimible en 3D (la pieza real)
  cad/nodo-suspension-datos.json   densidades para el visor web
"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
import json, os, struct

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(HERE, "..", "cad")
os.makedirs(CAD, exist_ok=True)

# ----------------- parámetros -----------------
# Dominio de diseño en voxels (el "bloque" inicial de material)
_N = int(os.environ.get("NODO_N", "32"))
nelx, nely, nelz = _N, _N, _N
volfrac = 0.22          # fracción de material a conservar (22% → se quita el 78%)
penal   = 3.0           # penalización SIMP (empuja a lleno/vacío)
rmin    = 1.6           # radio del filtro (controla el grosor mínimo de "hueso")
maxit   = int(os.environ.get("NODO_IT", "34"))
E0, Emin, nu = 1.0, 1e-9, 0.3

# ----------------- matriz de rigidez del hexaedro por integración de Gauss -----------------
# Elemento H8 trilineal sobre cubo unitario. KE = integral(B^T D B dV), Gauss 2x2x2.
# Orden de nodos locales (esquinas del cubo):
LOCAL = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
                  [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]], dtype=float)

def hex_stiffness(E, nu):
    a = E / ((1 + nu) * (1 - 2 * nu))
    D = a * np.array([
        [1 - nu, nu, nu, 0, 0, 0],
        [nu, 1 - nu, nu, 0, 0, 0],
        [nu, nu, 1 - nu, 0, 0, 0],
        [0, 0, 0, (1 - 2 * nu) / 2, 0, 0],
        [0, 0, 0, 0, (1 - 2 * nu) / 2, 0],
        [0, 0, 0, 0, 0, (1 - 2 * nu) / 2]])
    gp = np.array([-1, 1]) / np.sqrt(3.0)
    signs = 2 * LOCAL - 1                       # esquinas en coords naturales [-1,1]
    KE = np.zeros((24, 24))
    for xi in gp:
        for eta in gp:
            for zeta in gp:
                dN = np.zeros((3, 8))
                for i in range(8):
                    sx, sy, sz = signs[i]
                    dN[0, i] = 0.125 * sx * (1 + sy * eta) * (1 + sz * zeta)
                    dN[1, i] = 0.125 * sy * (1 + sx * xi) * (1 + sz * zeta)
                    dN[2, i] = 0.125 * sz * (1 + sx * xi) * (1 + sy * eta)
                J = dN @ LOCAL                  # jacobiano (cubo unitario)
                detJ = np.linalg.det(J)
                dNxyz = np.linalg.solve(J, dN)
                B = np.zeros((6, 24))
                for i in range(8):
                    bx, by, bz = dNxyz[:, i]
                    c = 3 * i
                    B[0, c] = bx; B[1, c + 1] = by; B[2, c + 2] = bz
                    B[3, c] = by; B[3, c + 1] = bx
                    B[4, c + 1] = bz; B[4, c + 2] = by
                    B[5, c] = bz; B[5, c + 2] = bx
                KE += (B.T @ D @ B) * detJ
    return KE

KE = hex_stiffness(1.0, nu)

# ----------------- numeración de GDL y conectividad (consistente con KE) -----------------
nele = nelx * nely * nelz
nx, ny, nz = nelx + 1, nely + 1, nelz + 1
ndof = 3 * nx * ny * nz

def gid(ix, iy, iz):
    return iz * (nx * ny) + iy * nx + ix        # id de nodo lexicográfico 0-based

# edofMat: 8 nodos locales de cada elemento -> 24 GDL, en el MISMO orden que KE
edofMat = np.zeros((nele, 24), dtype=np.int64)
_e = 0
_loc = LOCAL.astype(int)
for iz in range(nelz):
    for iy in range(nely):
        for ix in range(nelx):
            dofs = []
            for (lx, ly, lz) in _loc:
                n = gid(ix + lx, iy + ly, iz + lz)
                dofs += [3 * n, 3 * n + 1, 3 * n + 2]
            edofMat[_e] = dofs
            _e += 1

iK = np.kron(edofMat, np.ones((24, 1), dtype=np.int64)).flatten()
jK = np.kron(edofMat, np.ones((1, 24), dtype=np.int64)).flatten()

# ----------------- cargas y apoyos (la física de cada nodo) -----------------
# Cada unión del chasis tiene sus propios tubos de anclaje (caras empotradas) y
# sus propias fuerzas. Se elige con la variable de entorno NODO_TIPO.
NODO_TIPO = os.environ.get("NODO_TIPO", "susp_del")

F = np.zeros(ndof)
fixed = []

def fix_face(axis, at):
    """empotra una cara del bloque: axis 0=ix,1=iy,2=iz ; at=0 o max"""
    rng = [range(nelx + 1), range(nely + 1), range(nelz + 1)]
    for ix in rng[0]:
        for iy in rng[1]:
            for iz in rng[2]:
                coord = (ix, iy, iz)[axis]
                if coord == at:
                    n = gid(ix, iy, iz)
                    fixed.extend([3 * n, 3 * n + 1, 3 * n + 2])

def apply_load(ix, iy, iz, fx, fy, fz):
    n = gid(ix, iy, iz)
    F[3 * n] += fx; F[3 * n + 1] += fy; F[3 * n + 2] += fz

def load_box(ix0, ix1, iy0, iy1, iz0, iz1, fx, fy, fz):
    for ix in range(ix0, ix1):
        for iy in range(iy0, iy1):
            for iz in range(iz0, iz1):
                apply_load(ix, iy, iz, fx, fy, fz)

mx, my, mz = nelx, nely, nelz
if NODO_TIPO == "susp_del":
    # Nodo de suspensión delantera: bulkhead (ix=0) + estribo (iz=0) empotrados;
    # carga del coilover + brazo por la esquina superior-externa.
    fix_face(0, 0); fix_face(2, 0)
    load_box(mx, mx + 1, my - 3, my + 1, mz - 3, mz + 1, -0.3, 1.0, -0.4)
    load_box(mx, mx + 1, 0, 1, mz - 3, mz + 1, 0.0, 0.3, 0.0)
elif NODO_TIPO == "susp_tras":
    # Nodo trasero: riel de piso (iz=0) + mamparo trasero (ix=max) empotrados;
    # torre de coilover arriba + reacción del motor de cubo (empuje longitudinal).
    fix_face(2, 0); fix_face(0, mx)
    load_box(0, 3, my - 3, my + 1, mz - 3, mz + 1, 0.6, 1.0, 0.0)   # coilover
    load_box(0, 3, 0, 3, mz - 3, mz + 1, 1.0, 0.2, 0.0)            # empuje motor
elif NODO_TIPO == "arco_ppal":
    # Base del arco principal: piso (iz=0) empotrado; carga de vuelco desde arriba
    # (compresión + lateral) que baja por la pierna del arco hacia el estribo.
    fix_face(2, 0)
    load_box(mx // 2 - 2, mx // 2 + 2, my - 2, my + 1, mz // 2 - 2, mz // 2 + 2, 0.4, -1.0, 0.3)
elif NODO_TIPO == "cuna_bat":
    # Esquina de la cuna de batería: dos rieles (ix=0, iz=0) empotrados;
    # peso de la batería repartido en la cara superior (vertical hacia abajo).
    fix_face(0, 0); fix_face(2, 0)
    load_box(0, mx + 1, my - 2, my + 1, 0, mz + 1, 0.0, -1.0, 0.0)
elif NODO_TIPO == "pilar_a":
    # Nodo pilar A / tablero: estribo (iz=0) + mamparo (ix=0) empotrados;
    # carga del techo y parabrisas hacia abajo y atrás por la esquina superior.
    fix_face(2, 0); fix_face(0, 0)
    load_box(mx - 2, mx + 1, my - 3, my + 1, mz - 3, mz + 1, 0.5, -1.0, 0.0)
else:
    raise SystemExit(f"NODO_TIPO desconocido: {NODO_TIPO}")

fixed = np.unique(np.array(fixed))
free = np.setdiff1d(np.arange(ndof), fixed)

# ----------------- filtro de densidad (vectorizado) -----------------
print("preparando filtro...")
iH = []; jH = []; sH = []
nfil = int(nelx * nely * nelz * ((2 * (np.ceil(rmin) - 1) + 1) ** 3))
def eid(ix, iy, iz):
    return iz * (nelx * nely) + iy * nelx + ix   # mismo orden que edofMat
rc = int(np.ceil(rmin)) - 1
for iz in range(nelz):
    for iy in range(nely):
        for ix in range(nelx):
            e1 = eid(ix, iy, iz)
            for kz in range(max(iz - rc, 0), min(iz + rc + 1, nelz)):
                for kx in range(max(ix - rc, 0), min(ix + rc + 1, nelx)):
                    for ky in range(max(iy - rc, 0), min(iy + rc + 1, nely)):
                        e2 = eid(kx, ky, kz)
                        w = rmin - np.sqrt((ix-kx)**2 + (iy-ky)**2 + (iz-kz)**2)
                        if w > 0:
                            iH.append(e1); jH.append(e2); sH.append(w)
H = coo_matrix((sH, (iH, jH)), shape=(nele, nele)).tocsr()
Hs = np.array(H.sum(axis=1)).flatten()

# ----------------- bucle de optimización -----------------
x = np.full(nele, volfrac)
xPhys = x.copy()
print(f"optimizando {nelx}x{nely}x{nelz} = {nele} voxels, {ndof} GDL...")
for it in range(maxit):
    # FEA
    sK = ((KE.flatten()[:, None] * (Emin + xPhys ** penal * (E0 - Emin))[None, :]).flatten(order='F'))
    K = coo_matrix((sK, (iK, jK)), shape=(ndof, ndof)).tocsc()
    K = (K + K.T) * 0.5
    U = np.zeros(ndof)
    U[free] = spsolve(K[free, :][:, free], F[free])
    # sensibilidad de la compliance
    ce = np.einsum('ij,jk,ik->i', U[edofMat], KE, U[edofMat])
    c = np.sum((Emin + xPhys ** penal * (E0 - Emin)) * ce)
    dc = -penal * (E0 - Emin) * xPhys ** (penal - 1) * ce
    dv = np.ones(nele)
    # filtrado
    dc = np.asarray(H.dot(dc / Hs))
    dv = np.asarray(H.dot(dv / Hs))
    # OC (con protección numérica)
    dc = np.minimum(dc, 0.0)          # la sensibilidad de compliance es <= 0
    l1, l2, move = 1e-9, 1e9, 0.2
    B = np.maximum(-dc, 0.0) / dv     # >= 0
    while (l2 - l1) / (l1 + l2) > 1e-3:
        lmid = 0.5 * (l1 + l2)
        xnew = np.maximum(0.0, np.maximum(x - move,
                 np.minimum(1.0, np.minimum(x + move, x * np.sqrt(B / lmid)))))
        xPhys = np.asarray(H.dot(xnew) / Hs)
        if xPhys.sum() > volfrac * nele:
            l1 = lmid
        else:
            l2 = lmid
    ch = np.max(np.abs(xnew - x))
    x = xnew
    print(f"  it {it+1:2d}  compliance {c:8.2f}  vol {xPhys.mean():.3f}  cambio {ch:.3f}")
    if ch < 0.01:
        break

# ----------------- exportar STL (marching-cubes-lite por voxels llenos) -----------------
print("exportando STL...")
grid = xPhys.reshape((nelz, nely, nelx))  # [iz, iy, ix]
thr = 0.4
tris = []
# caras expuestas de cada voxel lleno (superficie del sólido)
faces = {
    (1,0,0): [(1,0,0),(1,1,0),(1,1,1),(1,0,1)],
    (-1,0,0):[(0,0,0),(0,0,1),(0,1,1),(0,1,0)],
    (0,1,0): [(0,1,0),(0,1,1),(1,1,1),(1,1,0)],
    (0,-1,0):[(0,0,0),(1,0,0),(1,0,1),(0,0,1)],
    (0,0,1): [(0,0,1),(1,0,1),(1,1,1),(0,1,1)],
    (0,0,-1):[(0,0,0),(0,1,0),(1,1,0),(1,0,0)],
}
sc = 0.15 / max(nelx, nely, nelz)  # ~150 mm de lado
def full(iz, ix, iy):
    if 0 <= iz < nelz and 0 <= ix < nelx and 0 <= iy < nely:
        return grid[iz, iy, ix] > thr
    return False
for iz in range(nelz):
    for iy in range(nely):
        for ix in range(nelx):
            if grid[iz, iy, ix] <= thr:
                continue
            for (dx, dy, dz), quad in [((1,0,0),faces[(1,0,0)]),((-1,0,0),faces[(-1,0,0)]),
                                       ((0,1,0),faces[(0,1,0)]),((0,-1,0),faces[(0,-1,0)]),
                                       ((0,0,1),faces[(0,0,1)]),((0,0,-1),faces[(0,0,-1)])]:
                if not full(iz+dz, ix+dx, iy+dy):
                    v = [((ix+q[0])*sc, (iy+q[1])*sc, (iz+q[2])*sc) for q in quad]
                    tris.append((v[0], v[1], v[2]))
                    tris.append((v[0], v[2], v[3]))

stl_path = os.path.join(CAD, f"nodo-{NODO_TIPO}.stl")
with open(stl_path, "wb") as f:
    f.write(b'\x00' * 80)
    f.write(struct.pack('<I', len(tris)))
    for (a, b, c2) in tris:
        ax = np.array(a); bx = np.array(b); cx = np.array(c2)
        n = np.cross(bx - ax, cx - ax); ln = np.linalg.norm(n)
        n = n / ln if ln > 0 else np.zeros(3)
        f.write(struct.pack('<3f', *n))
        for vv in (a, b, c2):
            f.write(struct.pack('<3f', *vv))
        f.write(struct.pack('<H', 0))

# datos para el visor web (voxels llenos con su densidad)
vox = []
for iz in range(nelz):
    for iy in range(nely):
        for ix in range(nelx):
            d = grid[iz, iy, ix]
            if d > thr:
                vox.append([ix, iy, iz, round(float(d), 3)])
json.dump({"nelx": nelx, "nely": nely, "nelz": nelz, "vox": vox, "tipo": NODO_TIPO,
           "compliance": round(float(c), 1), "volfrac": volfrac,
           "n_tris": len(tris)},
          open(os.path.join(CAD, f"nodo-{NODO_TIPO}-datos.json"), "w"))

masa_est = grid[grid > thr].size * (sc*1000)**3 * 1.24e-3  # nylon PA12 ~1.01, aquí densidad rellena
print(f"OK  {len(tris)} triángulos  |  {len(vox)} voxels de material  |  "
      f"compliance final {c:.1f}  |  STL: {stl_path}")
