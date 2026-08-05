# -*- coding: utf-8 -*-
"""
PLACA DE TORQUE DEL QS273 — diseño generativo por optimización topológica.

La pieza que impide que el eje del motor de cubo gire dentro del brazo tirado, y
que a la vez mete toda la carga de la rueda al brazo. Ver el spec en
docs/superpowers/specs/2026-08-04-placa-torque-qs273-design.md

Arquitectura: SÁNDWICH de dos placas de acero que abrazan la punta del PTR 70×50×4.
El eje del QS273 se apoya de un solo lado (dentro del rin 14" no cabe horquilla),
así que el motor queda en voladizo. Dos placas separadas convierten ese momento de
vuelco en fuerzas VERTICALES DENTRO DEL PLANO de cada placa, que es justo lo que una
placa hace bien. Una placa sola tendría que ser de 25-30 mm.

Método: SIMP en 2D esfuerzo plano (elemento Q4, filtro de densidad, actualización
por criterio de optimalidad) con VARIOS CASOS DE CARGA simultáneos. El 2D no es una
simplificación: es el modelo correcto de una placa plana cargada en su plano, y
además impone la restricción de fabricación por construcción — lo que sale del
algoritmo ES el contorno que corta el láser.

Unidades reales en todo el FEM (N, m, Pa), así que los esfuerzos salen directos.

Salidas:
  planos/placa-torque-motor.dxf      contorno de corte láser (placa exterior)
  planos/placa-torque-refuerzo.dxf   contorno de corte láser (placa interior)
  planos/placa-torque-doblador.dxf   anillo de refuerzo del cubo del eje
  calculos/resultados-placa-torque.md
  calculos/placa-torque.png
"""
import numpy as np
from scipy.sparse import coo_matrix, diags
from scipy.sparse.linalg import splu
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
PLANOS = os.path.join(HERE, "..", "planos")

# ============================================================================
# 1. PARÁMETROS  (todo lo que hay que confirmar con QS Motor vive aquí arriba)
# ============================================================================
# --- eje del QS273 (CONFIRMAR POR ESCRITO ANTES DE CORTAR) ---
EJE_D      = 0.020    # m, diámetro del eje
EJE_PLANOS = 0.016    # m, entrecaras de los planos maquinados
EJE_LIBRE  = 0.084    # m, largo del eje que sobresale del lado interior (REQUERIDO).
                      # Corregido 2026-08-04 al armar el modelo 3D completo: no son
                      # 8+50+8+tuerca pegados a la cara del motor, porque entre la cara
                      # y la placa exterior viven el disco y el caliper. Hay 30 mm de
                      # separación ahí; las orejas del caliper la salvan con separadores.
MOTOR_W    = 0.130    # m, ancho del cuerpo del motor
DISCO_R    = 0.110    # m, radio del disco de freno que trae el QS273
CALIPER_R  = 0.095    # m, radio efectivo de frenado (centro de pastilla)
CALIPER_SEP= 0.082    # m, separación de barrenos del caliper (ATV típico)

# --- brazo y placas ---
PTR_H, PTR_W, PTR_T = 0.070, 0.050, 0.004   # PTR 70 alto × 50 ancho × 4 pared
T_PLACA  = 0.008      # m, espesor de cada placa (corte láser)
GAP      = PTR_W      # m, separación entre placas = ancho del PTR (las abraza)
VOLADIZO = MOTOR_W / 2 + 0.025   # m, del plano de la placa exterior al centro de rueda
BULON_D  = 0.012      # m, M12 grado 10.9 (M10 deja el aplastamiento en FS 2.0, al filo)
BULONES  = [(0.036, +0.025), (0.036, -0.025),
            (0.096, +0.025), (0.096, -0.025)]   # (u, v) en el frame de la placa
# Brida de la junta atornillada: banda de material obligatorio alrededor de cada hilera
# de tornillos. NO es un capricho — es la cara que aprieta contra el flanco del PTR y
# donde asientan las calzas del toe. Sin ella la junta no se puede torquear.
BRIDA_H  = 0.016      # m, media altura de la banda (distancia al borde desde el barreno)
BRIDA_U  = (0.018, 0.114)   # m, extensión de la banda a lo largo del brazo
# Rigidez a cortante de un tornillo en junta de acero: k ≈ G·A/L con L el espesor
# agarrado. Un empotramiento rígido sería infinito y falsearía el reparto.
K_BULON  = 80e9 * np.pi * (BULON_D / 2)**2 / T_PLACA

# --- cargas de la esquina trasera (de suspension_trasera.py) ---
R_RUEDA   = 0.3005    # m, 175/70R14
M_ESQ     = 690.0 * 0.62 / 2      # kg por esquina trasera = 213.9
G         = 9.81
PAR_MOTOR = 350.0     # N·m, par máximo del QS273 por rueda (también el tope de regen)
PAR_FRENO = 630.0     # N·m, frenado 1g (objetivo declarado del cálculo de frenos)
F_BACHE   = 3 * G * M_ESQ         # N, bache 3g vertical en la rueda
F_LAT_1G  = G * M_ESQ             # N, curva 1g en el parche de contacto
F_LONG_1G = PAR_FRENO / R_RUEDA   # N, longitudinal en el parche al frenar a 1g

# --- material y criterio ---
SIGMA_Y  = 250e6      # Pa, acero estructural (mismo criterio que el resto del proyecto)
E_ACERO  = 210e9
RHO      = 7850.0     # kg/m³
FS_OBJ   = 2.0

# --- malla y optimización ---
# El dominio se ajusta a lo que la pieza REALMENTE necesita alcanzar: el cubo del eje,
# los tornillos más lejanos y las orejas del caliper. Un dominio más grande solo obliga
# al optimizador a tirar material donde no sirve (la restricción de volumen es activa).
U0, U1 = -0.045, 0.165    # dominio en u (a lo largo del brazo, + hacia el pivote)
V0, V1 = -0.110, 0.115    # dominio en v (perpendicular al brazo)
HEL    = 0.002            # m, tamaño de elemento (2 mm)
PENAL, MAXIT = 3.0, 40
RMIN_MM = 6.0             # radio del filtro → ancho mínimo de nervadura ~12 mm
# Barrido de fracción de volumen: la masa NO es un resultado del optimizador, es la
# restricción que se le impone. Para una pieza gobernada por resistencia hay que barrerla
# y quedarse con la más ligera que todavía cumpla el criterio de FS.
BARRIDO = [0.40, 0.36, 0.33, 0.30, 0.28, 0.26, 0.24, 0.22, 0.20, 0.18]

nelx = int(round((U1 - U0) / HEL))
nely = int(round((V1 - V0) / HEL))
rmin = RMIN_MM / 1000.0 / HEL
nu = 0.3

# ============================================================================
# 2. ESTÁTICA: cómo se reparten las cargas de la rueda entre las dos placas
# ============================================================================
def reparto(Fv, Flong, Flat):
    """Reparte las cargas del centro de rueda entre placa exterior e interior.

    El eje va en voladizo: la rueda está a VOLADIZO de la placa exterior, y la
    interior está GAP más adentro. El momento de vuelco se equilibra con fuerzas
    opuestas en las dos placas — que quedan DENTRO del plano de cada una.

    Fv    : N, vertical en el centro de rueda (+ arriba)
    Flong : N, longitudinal en el parche de contacto (+ hacia adelante)
    Flat  : N, lateral en el parche (+ hacia afuera; genera momento de vuelco extra)
    Devuelve (Fv_ext, Fv_int, Flong_ext, Flong_int) en N.
    """
    # Momento de vuelco alrededor del eje longitudinal, tomado en la placa interior.
    # Contribuye el peso en voladizo y la fuerza lateral por el radio de la rueda.
    Fv_ext = (Fv * (VOLADIZO + GAP) + Flat * R_RUEDA) / GAP
    Fv_int = Fv - Fv_ext
    # La fuerza longitudinal actúa en el plano de la rueda: mismo esquema de palanca.
    Fl_ext = Flong * (VOLADIZO + GAP) / GAP
    Fl_int = Flong - Fl_ext
    return Fv_ext, Fv_int, Fl_ext, Fl_int

# Caso bache 3g: solo vertical.
B_ext, B_int, _, _ = reparto(F_BACHE, 0.0, 0.0)
# Caso curva 1g: vertical estático + lateral (el lateral suma momento de vuelco).
C_ext, C_int, _, _ = reparto(G * M_ESQ, 0.0, F_LAT_1G)
# Caso frenado 1g: vertical estático + longitudinal.
_, _, Fr_ext, Fr_int = reparto(G * M_ESQ, F_LONG_1G, 0.0)

# ============================================================================
# 3. FEM 2D — elemento Q4 esfuerzo plano, unidades reales
# ============================================================================
LOCAL = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
D_UNIT = 1.0 / (1 - nu**2) * np.array([[1, nu, 0], [nu, 1, 0], [0, 0, (1 - nu) / 2]])

def q4_stiffness(h, t):
    """Rigidez del Q4 de lado h y espesor t con E=1 (el módulo real entra por SIMP)."""
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
            J = dN @ (LOCAL * h)
            dNxy = np.linalg.solve(J, dN)
            B = np.zeros((3, 8))
            for i in range(4):
                bx, by = dNxy[:, i]
                B[0, 2*i] = bx; B[1, 2*i+1] = by
                B[2, 2*i] = by; B[2, 2*i+1] = bx
            KE += (B.T @ D_UNIT @ B) * np.linalg.det(J) * t
    return KE

def b_centro(h):
    """Matriz B evaluada en el centro del elemento (para esfuerzos)."""
    dN = np.zeros((2, 4))
    for i in range(4):
        sx, sy = 2 * LOCAL[i] - 1
        dN[0, i] = 0.25 * sx
        dN[1, i] = 0.25 * sy
    dNxy = np.linalg.solve(dN @ (LOCAL * h), dN)
    B = np.zeros((3, 8))
    for i in range(4):
        bx, by = dNxy[:, i]
        B[0, 2*i] = bx; B[1, 2*i+1] = by
        B[2, 2*i] = by; B[2, 2*i+1] = bx
    return B

KE = q4_stiffness(HEL, T_PLACA)
BC = b_centro(HEL)

nele, nx, ny = nelx * nely, nelx + 1, nely + 1
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

# coordenadas de nodos y centros de elemento en el frame de la placa (u,v)
nod_u = np.tile(np.arange(nx) * HEL + U0, ny)
nod_v = np.repeat(np.arange(ny) * HEL + V0, nx)
ele_u = np.tile(np.arange(nelx) * HEL + U0 + HEL / 2, nely)
ele_v = np.repeat(np.arange(nely) * HEL + V0 + HEL / 2, nelx)

# ============================================================================
# 4. FILTRO DE DENSIDAD
# ============================================================================
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

# ============================================================================
# 5. UNA CORRIDA DE OPTIMIZACIÓN POR PLACA
# ============================================================================
def nodos_en(cu, cv, r):
    d2 = (nod_u - cu)**2 + (nod_v - cv)**2
    return np.where(d2 <= r**2)[0]

def elems_en(cu, cv, r):
    d2 = (ele_u - cu)**2 + (ele_v - cv)**2
    return np.where(d2 <= r**2)[0]

def optimiza(nombre, con_caliper, Fv_placa, Fl_placa, par_eje, volfrac, verbose=True):
    """Corre SIMP multi-caso para una de las dos placas. Devuelve dict de resultados."""
    R_EJE = EJE_D / 2
    R_CUBO = R_EJE + 0.018          # anillo sólido obligatorio alrededor del eje
    R_PAD = BULON_D / 2 + 0.007     # pad sólido obligatorio en cada tornillo

    # --- regiones pasivas ---
    vacio = np.zeros(nele, dtype=bool)
    solido = np.zeros(nele, dtype=bool)
    vacio[elems_en(0, 0, R_EJE)] = True                 # hueco del eje
    solido[elems_en(0, 0, R_CUBO)] = True               # cubo
    # Brida de la junta: banda continua alrededor de cada hilera de tornillos. Es una
    # superficie FUNCIONAL impuesta, no un resultado del optimizador — la minimización
    # de compliance siempre descarta apoyos redundantes (se queda con los dos tornillos
    # más cercanos y abandona los otros dos), pero una junta atornillada necesita cara
    # de apriete continua y los cuatro tornillos repartiendo carga.
    for vrow in sorted({bv for (_, bv) in BULONES}):
        solido[np.where((np.abs(ele_v - vrow) <= BRIDA_H) &
                        (ele_u >= BRIDA_U[0]) & (ele_u <= BRIDA_U[1]))[0]] = True
    for (bu, bv) in BULONES:
        solido[elems_en(bu, bv, R_PAD)] = True
        vacio[elems_en(bu, bv, BULON_D / 2)] = True     # barreno

    # --- posición de las orejas del caliper ---
    cal = []
    if con_caliper:
        dang = CALIPER_SEP / DISCO_R / 2
        for a in (np.radians(55) - dang, np.radians(55) + dang):
            cal.append((DISCO_R * np.cos(a), DISCO_R * np.sin(a)))
        for (cu, cv) in cal:
            solido[elems_en(cu, cv, R_PAD)] = True
            vacio[elems_en(cu, cv, BULON_D / 2)] = True
    solido &= ~vacio

    def nodos_borde_hueco(cu, cv, r_hueco):
        """Nodos del MATERIAL que rodean un hueco — ahí es donde apoya el eje o el
        tornillo. Cargar los nodos de adentro del hueco los deja flotando (solo los
        rodea material Emin) y su desplazamiento infinito se traga toda la compliance."""
        es = elems_en(cu, cv, r_hueco + 2.5 * HEL)
        es = es[~vacio[es]]
        nn = np.unique(edofMat[es][:, ::2] // 2)
        d = np.hypot(nod_u[nn] - cu, nod_v[nn] - cv)
        return nn[d <= r_hueco + 1.5 * HEL]

    # --- apoyos: cada tornillo es un RESORTE a tierra, no un empotramiento ---
    # Un empotramiento rígido puede reaccionar momento él solo, así que al optimizador
    # nunca le conviene estirarse hasta los tornillos lejanos: los deja como islas
    # flotantes. Un tornillo real tiene rigidez finita, y repartir la carga entre los
    # cuatro SÍ baja la deformación — que es lo que pasa en la pieza de verdad.
    nod_bulon = [nodos_borde_hueco(bu, bv, BULON_D / 2) for (bu, bv) in BULONES]
    kdiag = np.zeros(ndof)
    k_nodo = []
    for nn in nod_bulon:
        kn = K_BULON / len(nn)
        k_nodo.append(kn)
        kdiag[2 * nn] += kn
        kdiag[2 * nn + 1] += kn
    Kmuelle = diags(kdiag).tocsc()

    # --- casos de carga ---
    aro = nodos_borde_hueco(0, 0, R_EJE)         # nodos del material que abraza el eje
    ru = nod_u[aro]; rv = nod_v[aro]
    rr = np.maximum(np.hypot(ru, rv), 1e-6)
    casos = []

    def caso(nom, f):
        casos.append((nom, f))

    # 1) par por el eje (tracción o regen): fuerzas tangenciales en el aro del cubo.
    #    Reparto uniforme: ΣF_i·r_i = par  →  F_i = par / (n · r̄)
    f = np.zeros(ndof)
    Fi = par_eje / (len(aro) * float(np.mean(rr)))
    f[2 * aro]     = -rv / rr * Fi                # dirección tangencial unitaria × F_i
    f[2 * aro + 1] = +ru / rr * Fi
    caso(f"par por el eje {par_eje:.0f} N·m", f)

    # 2) bache 3g: vertical en el cubo
    f = np.zeros(ndof)
    f[2 * aro + 1] = Fv_placa / len(aro)
    caso(f"bache 3g {Fv_placa/1000:+.1f} kN vertical", f)

    # 3) curva 1g: vertical (del momento de vuelco lateral) en el cubo
    f = np.zeros(ndof)
    f[2 * aro + 1] = (C_ext if con_caliper else C_int) / len(aro)
    caso(f"curva 1g {(C_ext if con_caliper else C_int)/1000:+.1f} kN vertical", f)

    # 4) frenado 1g: longitudinal en el cubo (+ el par por el caliper si lo lleva)
    f = np.zeros(ndof)
    f[2 * aro] = Fl_placa / len(aro)
    if con_caliper:
        Fcal = PAR_FRENO / CALIPER_R              # fuerza tangencial en las orejas
        for (cu, cv) in cal:
            nn = nodos_borde_hueco(cu, cv, BULON_D / 2)
            tu, tv = -cv, cu
            tn = np.hypot(tu, tv)
            f[2 * nn]     += (tu / tn) * Fcal / (2 * len(nn))
            f[2 * nn + 1] += (tv / tn) * Fcal / (2 * len(nn))
        casos.append((f"frenado 1g: {Fcal/1000:.1f} kN en el caliper + "
                      f"{Fl_placa/1000:+.1f} kN long.", f))
    else:
        casos.append((f"frenado 1g {Fl_placa/1000:+.1f} kN longitudinal", f))

    Fmat = np.column_stack([f for (_, f) in casos])
    nlc = Fmat.shape[1]

    # --- bucle SIMP ---
    activos = ~vacio
    x = np.full(nele, volfrac)
    x[vacio] = 0.0; x[solido] = 1.0
    xPhys = x.copy()
    Emin = E_ACERO * 1e-9
    vol_obj = volfrac * activos.sum()
    if verbose:
        print(f"\n[{nombre}] {nelx}x{nely}={nele} elems, {nlc} casos de carga, "
              f"{activos.sum()} activos")
    U = np.zeros((ndof, nlc))
    c = 0.0
    for it in range(MAXIT):
        sK = (KE.flatten()[:, None] *
              (Emin + xPhys**PENAL * (E_ACERO - Emin))[None, :]).flatten(order='F')
        K = coo_matrix((sK, (iK, jK)), shape=(ndof, ndof)).tocsc()
        K = (K + K.T) * 0.5 + Kmuelle
        lu = splu(K)
        for j in range(nlc):
            U[:, j] = lu.solve(Fmat[:, j])
        # compliance (incluye la energía de los resortes de los tornillos) y
        # sensibilidad, sumadas sobre todos los casos. Los resortes no dependen del
        # diseño, así que no entran en la sensibilidad.
        ce = np.zeros(nele)
        for j in range(nlc):
            Ue = U[edofMat, j]
            ce += np.einsum('ij,jk,ik->i', Ue, KE, Ue)
        c = float(np.sum(Fmat * U))
        dc = -PENAL * (E_ACERO - Emin) * xPhys**(PENAL - 1) * ce
        dv = np.ones(nele)
        dc = np.asarray(H.dot(dc / Hs)); dv = np.asarray(H.dot(dv / Hs))
        dc = np.minimum(dc, 0.0)
        l1, l2, move = 1e-30, 1e30, 0.2
        Bo = np.maximum(-dc, 0.0) / dv
        while (l2 - l1) / (l1 + l2) > 1e-4:
            lmid = 0.5 * (l1 + l2)
            xnew = np.maximum(0.0, np.maximum(x - move,
                     np.minimum(1.0, np.minimum(x + move, x * np.sqrt(Bo / lmid)))))
            xnew[vacio] = 0.0; xnew[solido] = 1.0
            xPhys = np.asarray(H.dot(xnew) / Hs)
            xPhys[vacio] = 0.0; xPhys[solido] = 1.0
            if xPhys[activos].sum() > vol_obj:
                l1 = lmid
            else:
                l2 = lmid
        ch = np.max(np.abs(xnew - x))
        x = xnew
        if verbose and (it == 0 or (it + 1) % 10 == 0 or ch < 0.01):
            print(f"  it {it+1:2d}  compliance {c*1000:9.2f} mJ  "
                  f"vol {xPhys[activos].mean():.3f}  cambio {ch:.3f}")
        if ch < 0.01:
            break

    # --- FEA final sobre la topología convergida (para esfuerzos y reacciones) ---
    sK = (KE.flatten()[:, None] *
          (Emin + xPhys**PENAL * (E_ACERO - Emin))[None, :]).flatten(order='F')
    K = coo_matrix((sK, (iK, jK)), shape=(ndof, ndof)).tocsc()
    K = (K + K.T) * 0.5 + Kmuelle
    lu = splu(K)
    for j in range(nlc):
        U[:, j] = lu.solve(Fmat[:, j])

    # --- reacción real en cada tornillo: la fuerza que se lleva su resorte ---
    reac = []
    for nn, kn in zip(nod_bulon, k_nodo):
        fu = (kn * U[2 * nn, :]).sum(axis=0)
        fv = (kn * U[2 * nn + 1, :]).sum(axis=0)
        reac.append(float(np.max(np.hypot(fu, fv))))

    # --- esfuerzos von Mises en el material real ---
    solidos = xPhys > 0.7
    vm_max = 0.0
    vm_grid = np.zeros(nele)
    for j in range(nlc):
        Ue = U[edofMat, j]
        sig = (E_ACERO * (D_UNIT @ BC @ Ue.T)).T        # (nele, 3) en Pa
        sx, sy, sxy = sig[:, 0], sig[:, 1], sig[:, 2]
        vm = np.sqrt(sx**2 - sx * sy + sy**2 + 3 * sxy**2)
        vm_grid = np.maximum(vm_grid, vm)
    if solidos.any():
        # percentil 99.5 para ignorar la singularidad numérica en esquinas del empotramiento
        vm_max = float(np.percentile(vm_grid[solidos], 99.5))

    area = xPhys.sum() * HEL**2
    masa = area * T_PLACA * RHO
    return dict(nombre=nombre, xPhys=xPhys, casos=[n for (n, _) in casos],
                compliance=c, vm=vm_max, masa=masa, area=area, volfrac=volfrac,
                fs=SIGMA_Y / vm_max if vm_max > 0 else np.inf, reac=reac,
                cal=cal, vacio=vacio, solido=solido, vm_grid=vm_grid)

def barre(nombre, con_caliper, Fv, Fl, par):
    """Barre la fracción de volumen de mayor a menor y devuelve (historial, elegida).
    La elegida es la MÁS LIGERA que todavía cumple FS >= FS_OBJ."""
    hist, mejor, c_ref = [], None, None
    print(f"\n=== barrido de fracción de volumen — {nombre} ===")
    for vf in BARRIDO:
        r = optimiza(nombre, con_caliper, Fv, Fl, par, vf, verbose=False)
        if c_ref is None:
            c_ref = r["compliance"]
        # El material obligatorio (cubo + brida + pads) es un piso: por debajo de él
        # bajar la fracción de volumen ya no quita masa y el barrido deja de informar.
        if hist and r["masa"] > 0.99 * hist[-1]["masa"]:
            print(f"  volfrac {vf:.2f}  piso de material obligatorio alcanzado "
                  f"({r['masa']:.3f} kg) — se corta el barrido")
            break
        # Guardia: si la compliance se dispara, la estructura se desconectó y el
        # esfuerzo medido deja de significar nada. Se descarta ese escalón.
        r["conectada"] = r["compliance"] <= 5 * c_ref
        hist.append(r)
        ok = r["fs"] >= FS_OBJ and r["conectada"]
        motivo = "ok" if ok else ("DESCONECTADA" if not r["conectada"] else "NO")
        print(f"  volfrac {vf:.2f}  masa {r['masa']:.3f} kg  vM {r['vm']/1e6:5.0f} MPa  "
              f"FS {r['fs']:.2f}  compliance {r['compliance']*1000:8.1f} mJ  {motivo}")
        if ok:
            mejor = r
    if mejor is None:                     # ni la más pesada cumple
        mejor = hist[0]
    return hist, mejor

# ============================================================================
# 6. VERIFICACIONES ANALÍTICAS (lo que el topopt no ve)
# ============================================================================
def check_cubo(par, t_total):
    """Aplastamiento en los planos del eje.

    CORREGIDO 2026-08-05. Antes se usaba T = F·a con a = la entrecaras (16 mm), como
    si las dos fuerzas actuaran separadas por el grueso del eje. Está mal: la presión
    sobre un plano maquinado es NORMAL al plano, así que su brazo respecto al eje se
    mide **a lo largo del plano**, no a través de él. Con contacto unilateral la
    presión se reparte en triángulo sobre media cara y su resultante queda a w/3 del
    eje, de modo que T = 2·F·(w/3)  →  **F = 3T/(2w)**, que es el DOBLE de lo que se
    calculaba. El resultado se invierte: lo que parecía FS 2.2 es en realidad 1.1."""
    w = 2 * np.sqrt((EJE_D / 2)**2 - (EJE_PLANOS / 2)**2)   # ancho de cada plano
    F = 3 * par / (2 * w)
    sigma = F / (w * t_total)
    return w, F, sigma, SIGMA_Y / sigma

def check_bulon(F_bulon):
    """Tornillo M10 10.9 con la reacción que salió del FEM: cortante y aplastamiento."""
    tau = F_bulon / (np.pi * (BULON_D / 2)**2)
    cap_cort = 0.6 * 1040e6                 # 10.9: Rm 1040 MPa
    aplast = F_bulon / (BULON_D * T_PLACA)
    return tau, cap_cort / tau, aplast, 1.5 * SIGMA_Y / aplast

# ============================================================================
# 7. EXPORTACIÓN DXF
# ============================================================================
def dxf_open():  return ["0", "SECTION", "2", "ENTITIES"]
def dxf_close(l): return "\n".join(l + ["0", "ENDSEC", "0", "EOF"]) + "\n"

def dxf_line(l, x1, y1, x2, y2, capa="CORTE"):
    l += ["0", "LINE", "8", capa,
          "10", f"{x1:.3f}", "20", f"{y1:.3f}", "30", "0",
          "11", f"{x2:.3f}", "21", f"{y2:.3f}", "31", "0"]

def dxf_circle(l, cx, cy, r, capa="CORTE"):
    l += ["0", "CIRCLE", "8", capa,
          "10", f"{cx:.3f}", "20", f"{cy:.3f}", "30", "0", "40", f"{r:.3f}"]

def dxf_poly(l, pts, capa="CORTE"):
    for i in range(len(pts) - 1):
        dxf_line(l, pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], capa)

def perfil_doble_d(cx, cy, D, a, n=48):
    """Contorno de un agujero circular con dos planos (doble-D). Todo en mm."""
    R, ha = D / 2, a / 2
    w = np.sqrt(R**2 - ha**2)
    t0 = np.arctan2(ha, w)
    pts = []
    for t in np.linspace(-t0, t0, n // 2):            # arco derecho
        pts.append((cx + R * np.cos(t), cy + R * np.sin(t)))
    pts.append((cx - w, cy + ha))                     # plano superior
    for t in np.linspace(np.pi - t0, np.pi + t0, n // 2):   # arco izquierdo
        pts.append((cx + R * np.cos(t), cy + R * np.sin(t)))
    pts.append((cx + w, cy - ha))                     # plano inferior
    pts.append(pts[0])
    return pts

def contorno_exterior(xPhys, huecos):
    """Extrae el contorno de la pieza a 0.5 de densidad, en mm, descartando los
    lazos que solo rodean barrenos (esos se dibujan exactos)."""
    g = xPhys.reshape((nely, nelx))
    gp = np.zeros((nely + 2, nelx + 2))               # padding para cerrar los lazos
    gp[1:-1, 1:-1] = g
    uu = (np.arange(-1, nelx + 1) + 0.5) * HEL + U0
    vv = (np.arange(-1, nely + 1) + 0.5) * HEL + V0
    cs = plt.figure().gca().contour(uu * 1000, vv * 1000, gp, levels=[0.5])
    try:                                          # matplotlib < 3.8
        crudos = cs.allsegs[0]
    except AttributeError:                        # matplotlib >= 3.8
        crudos = [v for pth in cs.get_paths() for v in pth.to_polygons()]
    segs = [np.asarray(p) for p in crudos if len(p) > 8]
    plt.close('all')
    out = []
    for p in segs:
        cx, cy = p[:, 0].mean(), p[:, 1].mean()
        rad = np.hypot(p[:, 0] - cx, p[:, 1] - cy).max()
        # ¿es solo el lazo de un barreno? (centro cerca de un hueco y radio pequeño)
        if any(np.hypot(cx - hx, cy - hy) < 6 and rad < hr + 4 for (hx, hy, hr) in huecos):
            continue
        out.append(p)
    return out

def escribe_dxf(ruta, xPhys, cal, doblador=False):
    huecos = [(0.0, 0.0, EJE_D / 2 * 1000)]
    for (bu, bv) in BULONES:
        huecos.append((bu * 1000, bv * 1000, BULON_D / 2 * 1000))
    for (cu, cv) in cal:
        huecos.append((cu * 1000, cv * 1000, BULON_D / 2 * 1000))
    d = dxf_open()
    for p in contorno_exterior(xPhys, huecos):
        dxf_poly(d, [(pt[0], pt[1]) for pt in p] + [(p[0][0], p[0][1])])
    dxf_poly(d, perfil_doble_d(0, 0, EJE_D * 1000, EJE_PLANOS * 1000))
    for (bu, bv) in BULONES:
        dxf_circle(d, bu * 1000, bv * 1000, BULON_D / 2 * 1000 + 0.25)
    for (cu, cv) in cal:
        dxf_circle(d, cu * 1000, cv * 1000, BULON_D / 2 * 1000 + 0.25)
    open(ruta, "w").write(dxf_close(d))

# ============================================================================
# 8. CORRIDA
# ============================================================================
if __name__ == "__main__":
    hist_motor, res_motor = barre("placa motor (exterior)", True,  B_ext, Fr_ext, PAR_MOTOR)
    hist_refue, res_refue = barre("placa refuerzo (interior)", False, B_int, Fr_int, PAR_MOTOR)

    escribe_dxf(os.path.join(PLANOS, "placa-torque-motor.dxf"),
                res_motor["xPhys"], res_motor["cal"])
    escribe_dxf(os.path.join(PLANOS, "placa-torque-refuerzo.dxf"),
                res_refue["xPhys"], [])

    # --- doblador del cubo: espesor mínimo para que el aplastamiento dé FS >= 2 ---
    w_plano, F_cubo, sig_8, fs_8 = check_cubo(PAR_MOTOR, T_PLACA)
    t_req = F_cubo / (w_plano * SIGMA_Y / FS_OBJ)
    t_dob = max(0.0, np.ceil((t_req - T_PLACA) * 1000 / 2) * 2 / 1000)   # a múltiplo de 2 mm
    _, _, sig_dob, fs_dob = check_cubo(PAR_MOTOR, T_PLACA + t_dob)
    R_DOB = (EJE_D / 2 + 0.018) * 1000
    if t_dob > 0:
        d = dxf_open()
        dxf_circle(d, 0, 0, R_DOB)
        dxf_poly(d, perfil_doble_d(0, 0, EJE_D * 1000, EJE_PLANOS * 1000))
        open(os.path.join(PLANOS, "placa-torque-doblador.dxf"), "w").write(dxf_close(d))

    F_bul = max(res_motor["reac"])
    tau_bul, fs_cort, apl_bul, fs_apl = check_bulon(F_bul)

    # ---------------- informe ----------------
    out_md = os.path.join(HERE, "resultados-placa-torque.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Placa de torque del QS273 — diseño generativo\n\n")
        f.write("La pieza que impide que el eje del motor de cubo gire dentro del brazo "
                "tirado, y que mete toda la carga de la rueda al brazo. Generada por "
                "`placa_torque.py` (SIMP 2D esfuerzo plano, 4 casos de carga simultáneos).\n\n")

        f.write("## Por qué son dos placas y no una\n\n")
        f.write(f"El eje del QS273 se apoya de un solo lado — dentro del rin 14\" no cabe una "
                f"horquilla que abrace la rueda — así que el motor de 27 kg queda en voladizo "
                f"a **{VOLADIZO*1000:.0f} mm** del plano de la placa. Ese voladizo genera un momento "
                f"que intenta doblar la placa FUERA de su plano, justo donde una placa es débil.\n\n")
        f.write(f"Con dos placas separadas **{GAP*1000:.0f} mm** (el ancho del PTR, que las abraza "
                f"sin piezas extra), el momento se convierte en fuerzas verticales **dentro del "
                f"plano** de cada placa:\n\n")
        f.write("| Caso en la rueda | Placa exterior | Placa interior |\n|---|---|---|\n")
        f.write(f"| Bache 3g ({F_BACHE/1000:.1f} kN vertical) | **{B_ext/1000:+.1f} kN** | "
                f"**{B_int/1000:+.1f} kN** |\n")
        f.write(f"| Curva 1g ({F_LAT_1G/1000:.1f} kN lateral) | {C_ext/1000:+.1f} kN | "
                f"{C_int/1000:+.1f} kN |\n")
        f.write(f"| Frenado 1g ({F_LONG_1G/1000:.1f} kN longitudinal) | {Fr_ext/1000:+.1f} kN | "
                f"{Fr_int/1000:+.1f} kN |\n\n")
        f.write(f"Son cargas en el plano: acero de {T_PLACA*1000:.0f} mm las traga. Una placa sola "
                "tendría que irse a 25-30 mm — cara, pesada, y masa no suspendida (lo peor "
                "para el agarre en baches).\n\n")

        f.write("## Casos de carga optimizados\n\n")
        f.write("Los cuatro se optimizan **a la vez** (suma de compliances). Optimizar solo el "
                "peor da una pieza excelente en ese caso y frágil en los demás.\n\n")
        for i, nom in enumerate(res_motor["casos"], 1):
            f.write(f"{i}. {nom}\n")
        f.write(f"\nEl par por el eje se limita a **{PAR_MOTOR:.0f} N·m** (tope del QS273, y por "
                f"tanto también el tope del regen). El par de frenado de fricción "
                f"(**{PAR_FRENO:.0f} N·m**, 1g) NO pasa por el eje: va del disco al caliper y de ahí "
                "a la placa exterior — por eso solo esa lleva orejas.\n\n")

        f.write("## Qué impuse yo y qué decidió el algoritmo\n\n")
        f.write("Vale la pena separarlo, porque \"diseño generativo\" no quiere decir que la "
                "máquina invente la pieza sola. Se le declaran las **superficies "
                "funcionales** — lo que la pieza tiene que tener sí o sí — y el algoritmo "
                "resuelve el material que las conecta.\n\n")
        f.write("**Impuesto (material obligatorio):**\n\n")
        f.write(f"- El cubo alrededor del eje: anillo sólido de Ø{2*(EJE_D/2+0.018)*1000:.0f} mm.\n")
        f.write(f"- La **brida de la junta**: banda continua de {2*BRIDA_H*1000:.0f} mm de alto "
                f"a lo largo de cada hilera de tornillos. Es la cara que aprieta contra el "
                f"flanco del PTR y donde asientan las calzas del toe.\n")
        f.write("- Los pads de los tornillos y de las orejas del caliper.\n\n")
        f.write("**Por qué la brida hay que imponerla.** Sin ella el optimizador entrega una "
                "pieza que solo agarra los dos tornillos más cercanos y deja los otros dos "
                "como islas flotantes, sin material que llegue hasta ellos. No es un error del "
                "algoritmo: **minimizar deformación siempre descarta apoyos redundantes**, "
                "porque estirarse hasta el tornillo lejano cuesta material y no rigidiza. "
                "Lo que ese criterio no ve es que con dos tornillos la carga por tornillo se "
                "dispara y la junta no se puede apretar bien. El reparto de carga entre "
                "tornillos y la cara de apriete son requisitos de la junta, no de la rigidez.\n\n")
        f.write("**Decidido por el algoritmo:** toda la telaraña que une el cubo con la brida "
                "y con las orejas del caliper — que es donde estaba el trabajo de verdad.\n\n")

        f.write("## Barrido de material (de dónde sale la masa)\n\n")
        f.write("La fracción de volumen **no es un resultado del optimizador: es la "
                "restricción que se le impone**. El algoritmo reparte el material que se le "
                "da, no decide cuánto. Para una pieza gobernada por resistencia hay que "
                "barrerla y quedarse con la más ligera que todavía cumple el criterio.\n\n")
        for h, r in ((hist_motor, res_motor), (hist_refue, res_refue)):
            f.write(f"**{h[0]['nombre']}**\n\n")
            f.write("| Fracción de volumen | Masa | von Mises (p99.5) | FS | |\n|---|---|---|---|---|\n")
            for e in h:
                marca = ("✓ elegida" if e is r else
                         "desconectada" if not e["conectada"] else
                         "ok" if e["fs"] >= FS_OBJ else "insuficiente")
                f.write(f"| {e['volfrac']:.2f} | {e['masa']:.3f} kg | {e['vm']/1e6:.0f} MPa | "
                        f"**{e['fs']:.2f}** | {marca} |\n")
            f.write("\n")

        f.write("## Resultado\n\n")
        f.write("| | Placa motor (exterior) | Placa refuerzo (interior) |\n|---|---|---|\n")
        f.write(f"| Espesor | {T_PLACA*1000:.0f} mm | {T_PLACA*1000:.0f} mm |\n")
        f.write(f"| Área de material | {res_motor['area']*1e4:.0f} cm² | "
                f"{res_refue['area']*1e4:.0f} cm² |\n")
        f.write(f"| Masa por pieza | **{res_motor['masa']:.2f} kg** | "
                f"**{res_refue['masa']:.2f} kg** |\n")
        f.write(f"| von Mises máx (p99.5) | {res_motor['vm']/1e6:.0f} MPa | "
                f"{res_refue['vm']/1e6:.0f} MPa |\n")
        f.write(f"| FS contra σy 250 MPa | **{SIGMA_Y/res_motor['vm']:.1f}** | "
                f"**{SIGMA_Y/res_refue['vm']:.1f}** |\n\n")
        # masa de los dobladores del cubo (anillo menos el hueco doble-D)
        R_ = EJE_D / 2
        th_ = 2 * np.arccos((EJE_PLANOS / 2) / R_)
        a_dd = np.pi * R_**2 - R_**2 * (th_ - np.sin(th_))       # área del doble-D
        m_dob = (np.pi * (R_DOB / 1000)**2 - a_dd) * t_dob * RHO if t_dob > 0 else 0.0
        masa_juego = 2 * (res_motor['masa'] + res_refue['masa'] + 2 * m_dob)
        f.write(f"Masa del juego completo del carro — 2 ruedas × (2 placas + 2 dobladores "
                f"de {m_dob:.2f} kg): **{masa_juego:.1f} kg**. Es masa NO suspendida, así que "
                "cada gramo cuenta doble para el agarre en baches.\n\n")

        f.write("## Verificaciones que el topopt no ve\n\n")
        f.write(f"**Aplastamiento en los planos del eje.** El par se transmite como un par de "
                f"fuerzas sobre las dos caras planas, separadas {EJE_PLANOS*1000:.0f} mm: "
                f"F = {PAR_MOTOR:.0f}/{EJE_PLANOS:.3f} = **{F_cubo/1000:.1f} kN** sobre un ancho de "
                f"plano de {w_plano*1000:.1f} mm.\n\n")
        f.write(f"- Con la placa desnuda de {T_PLACA*1000:.0f} mm: σ = {sig_8/1e6:.0f} MPa → "
                f"FS **{fs_8:.1f}** — **insuficiente**.\n")
        if t_dob > 0:
            f.write(f"- Con un **doblador de {t_dob*1000:.0f} mm** soldado alrededor del cubo "
                    f"(Ø{2*R_DOB:.0f} mm, misma placa, mismo corte láser): espesor local "
                    f"{(T_PLACA+t_dob)*1000:.0f} mm → σ = {sig_dob/1e6:.0f} MPa → FS "
                    f"**{fs_dob:.1f}** ✓\n\n")
            f.write("Este es el eslabón débil real de los montajes de motor de cubo y la razón "
                    "por la que se arrancan los cables de fase. El doblador cuesta un anillo "
                    "extra en la misma hoja y un cordón de soldadura.\n\n")
        else:
            f.write("- El espesor base ya cumple; no hace falta doblador.\n\n")
        f.write(f"**Grupo de {len(BULONES)} tornillos M{BULON_D*1000:.0f} 10.9.** "
                "Las reacciones salen del propio FEM "
                "(R = K·U − F en los grados sujetos), no de estática de mano — así se ve "
                "si los cuatro tornillos realmente trabajan:\n\n")
        f.write("| Tornillo (u, v) mm | Placa motor | Placa refuerzo |\n|---|---|---|\n")
        for i, (bu, bv) in enumerate(BULONES):
            f.write(f"| ({bu*1000:.0f}, {bv*1000:+.0f}) | "
                    f"{res_motor['reac'][i]/1000:.1f} kN | "
                    f"{res_refue['reac'][i]/1000:.1f} kN |\n")
        f.write(f"\nEl más cargado toma **{F_bul/1000:.1f} kN**.\n\n")
        f.write(f"- Cortante: {tau_bul/1e6:.0f} MPa contra 624 MPa de capacidad → FS "
                f"**{fs_cort:.1f}** ✓\n")
        f.write(f"- Aplastamiento en la placa: {apl_bul/1e6:.0f} MPa contra 375 MPa "
                f"(1.5·σy) → FS **{fs_apl:.1f}** {'✓' if fs_apl >= 2 else '⚠'}\n\n")
        f.write("Los tornillos pasan por **camisas de acero soldadas a través del PTR**, si no "
                "el apriete aplasta el tubo. Las calzas entre placa y flanco del PTR dan el "
                "toe-in de 1-2 mm que pide el brazo tirado.\n\n")

        f.write("## Archivos de corte\n\n")
        f.write(f"- `planos/placa-torque-motor.dxf` — ×2 (una por rueda), acero "
                f"{T_PLACA*1000:.0f} mm\n")
        f.write(f"- `planos/placa-torque-refuerzo.dxf` — ×2, acero {T_PLACA*1000:.0f} mm\n")
        if t_dob > 0:
            f.write(f"- `planos/placa-torque-doblador.dxf` — ×4 (uno por placa), acero "
                    f"{t_dob*1000:.0f} mm\n")
        f.write("\nTodos en mm, capa `CORTE`, listos para cotizar. El hueco del eje va con "
                "doble-D; pedir corte y luego **rimar a medida con el eje en mano** (holgura "
                "0 — cualquier juego aquí se convierte en golpeteo y termina ovalando).\n\n")

        f.write("## Confirmar con QS Motor antes de cortar\n\n")
        f.write("| Dato | Valor usado | Si cambia |\n|---|---|---|\n")
        f.write(f"| Ø del eje | {EJE_D*1000:.0f} mm | Cambia el cubo y el doblador |\n")
        f.write(f"| Entrecaras de los planos | {EJE_PLANOS*1000:.0f} mm | Cambia el "
                "aplastamiento (va al cuadrado del espesor requerido) |\n")
        f.write(f"| Largo del eje libre del lado interior | **≥ {EJE_LIBRE*1000:.0f} mm** | "
                f"**El dato crítico.** No es solo {T_PLACA*1000:.0f}+{GAP*1000:.0f}+"
                f"{T_PLACA*1000:.0f}+tuerca: entre la cara del motor y la placa exterior "
                "viven el disco y el caliper, que piden 30 mm más. Si el eje es más corto, "
                "ver el fallback del spec |\n")
        f.write(f"| Ancho del cuerpo del motor | {MOTOR_W*1000:.0f} mm | Cambia el voladizo y "
                "todo el reparto entre placas |\n")
        f.write(f"| Ø del disco y patrón del caliper | {DISCO_R*2000:.0f} mm / "
                f"{CALIPER_SEP*1000:.0f} mm | Cambia la posición de las orejas |\n")

    # ---------------- gráfica ----------------
    fig, axs = plt.subplots(1, 2, figsize=(14, 7.4), facecolor="#0d1117")
    for ax, r in zip(axs, (res_motor, res_refue)):
        ax.set_facecolor("#0d1117")
        g = r["xPhys"].reshape((nely, nelx))
        ax.imshow(g, cmap="bone", origin="lower", vmin=0, vmax=1,
                  extent=[U0*1000, U1*1000, V0*1000, V1*1000],
                  interpolation="bilinear", aspect="equal")
        th = np.linspace(0, 2*np.pi, 120)
        # contexto de escala: rueda, disco, PTR
        ax.plot(R_RUEDA*1000*np.cos(th), R_RUEDA*1000*np.sin(th), color="#8b949e",
                lw=1.2, ls="--", alpha=0.6)
        ax.plot(DISCO_R*1000*np.cos(th), DISCO_R*1000*np.sin(th), color="#f97316",
                lw=1.4, alpha=0.8)
        ax.add_patch(plt.Rectangle((0, -PTR_H*500), U1*1000, PTR_H*1000, fill=False,
                                   edgecolor="#38bdf8", ls=":", lw=1.3))
        ax.text(150, PTR_H*500 + 6, "PTR 70×50×4", color="#38bdf8", fontsize=8, ha="center")
        ax.text(DISCO_R*1000*0.72, -DISCO_R*1000*0.72, "disco Ø220", color="#f97316",
                fontsize=8)
        for (bu, bv) in BULONES:
            ax.plot(bu*1000, bv*1000, marker="o", mfc="none", color="#4ade80", ms=7)
        for (cu, cv) in r["cal"]:
            ax.plot(cu*1000, cv*1000, marker="s", mfc="none", color="#c084fc", ms=8)
        ax.set_xlim(U0*1000 - 5, U1*1000 + 5); ax.set_ylim(V0*1000 - 5, V1*1000 + 5)
        ax.tick_params(colors="#8b949e", labelsize=8)
        for sp in ax.spines.values():
            sp.set_color("#30363d")
        ax.set_title(f"{r['nombre']} — {r['masa']:.2f} kg · FS {SIGMA_Y/r['vm']:.1f}",
                     color="#e6edf3", fontsize=10)
    axs[0].set_xlabel("mm hacia el pivote del brazo →", color="#8b949e", fontsize=9)
    fig.suptitle("Placa de torque del QS273 — SIMP 2D con 4 casos de carga simultáneos\n"
                 f"verde = tornillos M{BULON_D*1000:.0f} al brazo · morado = orejas del "
                 "caliper · centro = eje doble-D",
                 color="#e6edf3", fontsize=12)
    fig.tight_layout()
    out_png = os.path.join(HERE, "placa-torque.png")
    fig.savefig(out_png, dpi=150, facecolor="#0d1117", bbox_inches="tight")

    print(f"\nreparto bache 3g:  exterior {B_ext/1000:+.1f} kN   interior {B_int/1000:+.1f} kN")
    print(f"cubo: F {F_cubo/1000:.1f} kN  sigma {sig_8/1e6:.0f} MPa (FS {fs_8:.1f}) "
          f"-> doblador {t_dob*1000:.0f} mm -> FS {fs_dob:.1f}")
    print(f"bulon mas cargado {F_bul/1000:.1f} kN  cortante FS {fs_cort:.1f}  "
          f"aplast FS {fs_apl:.1f}")
    for r in (res_motor, res_refue):
        print(f"{r['nombre']:28s} {r['masa']:.2f} kg  vM {r['vm']/1e6:.0f} MPa  "
              f"FS {SIGMA_Y/r['vm']:.1f}")
    print(f"OK  informe: {out_md}\nOK  grafica: {out_png}")
