# -*- coding: utf-8 -*-
"""
DIRECCIÓN — geometría de Ackermann, relación, esfuerzo y círculo de giro.

La suspensión delantera ya fijó los puntos duros por barrido numérico (camber,
caster, bump steer 0.04°/25mm). Lo que faltaba es la DIRECCIÓN propiamente dicha:
cuánto gira cada rueda respecto de la otra (Ackermann), cuántas vueltas de volante,
qué tan pesado queda sin servo y en cuánto espacio da la vuelta.

Método: al girar el volante a una altura de suspensión dada, las rótulas LBJ y UBJ
NO se mueven — la mangueta simplemente rota alrededor del eje de kingpin. Eso
convierte el problema en una sola incógnita (el ángulo de rotación ψ) sujeta a que
el tie rod conserve su largo. Se resuelve exacto para las dos ruedas y de ahí salen
los ángulos reales de cada una, sin fórmulas aproximadas.

Toda la geometría se importa de `suspension_delantera.py` para que no haya dos
verdades: si allá se mueve un punto, aquí cambia solo.

Salidas:
  calculos/resultados-direccion.md
  calculos/direccion.png
"""
import numpy as np
from scipy.optimize import fsolve
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import suspension_delantera as sd          # re-genera su propio informe (idempotente)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ============================================================================
# 1. DATOS
# ============================================================================
BATALLA = 2.13          # m, eje delantero x=550 → eje trasero x=2680
TROCHA_DEL = 2 * sd.W0[2]
MASA = 690.0
DIST_DEL = sd.DIST_DEL
R_RUEDA = sd.R_RUEDA
G = 9.81

# --- objetivos ---
ACK_OBJ = 85.0          # % de Ackermann buscado (carro de calle/terreno, no pista)
# El bump steer MANDA sobre el Ackermann: uno hace que el carro se dirija solo al
# pasar un tope (seguridad), el otro solo desgasta llanta en maniobra lenta.
BS_PREF = 0.060         # °/25 mm, tope preferido — se busca el mejor Ackermann bajo él
BS_MAX = 0.100          # °/25 mm, tope duro (el heredado es 0.043)
DELTA_REF = 20.0        # ° de la rueda exterior donde se mide el Ackermann

# --- cremallera y volante ---
P_RACK = 0.045          # m de carrera de cremallera por vuelta de volante (manual típica)
D_VOLANTE = 0.330       # m
S_RACK_MAX = 0.075      # m de carrera de cremallera a cada lado (tope físico típico)
P_LLANTA = 2.2e5        # Pa, presión de inflado
MU_PISO = 0.80          # coeficiente llanta-piso para el par de pivotamiento parado

# --- puntos duros heredados (NO se tocan: fijan camber/caster/bump steer) ---
LBJ, UBJ = sd.LBJ0, sd.UBJ0
TR0 = sd.TR0
RACK0 = sd.RACK

# ============================================================================
# 2. CINEMÁTICA DE GIRO (exacta, una sola incógnita)
# ============================================================================
def gira(rack, tr0, d_tr, s_lat, psi0=0.0):
    """Rota la mangueta alrededor del kingpin hasta que el tie rod cierre.
    s_lat: desplazamiento lateral de la cremallera (m, + hacia +z).
    Devuelve (psi, ángulo de rueda en grados, ok). ok=False si el varillaje no
    cierra — pasa cuando el tie rod se queda corto o llega a punto muerto."""
    rk = rack + np.array([0.0, 0.0, s_lat])
    def eq(x):
        tr = sd.rot_eje(LBJ, UBJ, x[0], tr0)
        return [np.linalg.norm(tr - rk) - d_tr]
    sol, info, ier, _ = fsolve(eq, [psi0], full_output=True)
    psi = float(sol[0])
    ok = ier == 1 and abs(info["fvec"][0]) < 1e-8 and abs(psi) < 1.2
    W = sd.rot_eje(LBJ, UBJ, psi, sd.W0)
    S = sd.rot_eje(LBJ, UBJ, psi, sd.S0)
    a = (S - W) / np.linalg.norm(S - W)
    f = np.cross(np.array([0.0, 1.0, 0.0]), a)      # dirección de rodadura
    return psi, np.degrees(np.arctan2(-f[2], f[0])), ok

def par_ruedas(rack, tr0, s, psi_prev=(0.0, 0.0)):
    """Ángulos de las dos ruedas para un desplazamiento s de la cremallera.
    Por simetría especular, la rueda derecha con +s equivale a la izquierda con −s
    cambiada de signo."""
    d_tr = np.linalg.norm(tr0 - rack)
    pL, dL, okL = gira(rack, tr0, d_tr, +s, psi_prev[0])
    pR, dR_, okR = gira(rack, tr0, d_tr, -s, psi_prev[1])
    return dL, -dR_, (pL, pR), (okL and okR)

def curva_giro(rack, tr0, s_max=S_RACK_MAX, n=60):
    """Ángulos exterior/interior a lo largo de la carrera de cremallera, cortando
    donde el varillaje deja de cerrar."""
    ss, out, inn = [], [], []
    psi = (0.0, 0.0)
    for s in np.linspace(0, s_max, n):
        dL, dR, psi, ok = par_ruedas(rack, tr0, s, psi)
        if not ok:
            break
        ss.append(s); out.append(min(abs(dL), abs(dR))); inn.append(max(abs(dL), abs(dR)))
    return np.array(ss), np.array(out), np.array(inn)

def inner_ideal(d_o):
    """Ángulo interior que pide la geometría de giro para un exterior dado."""
    r = BATALLA / np.tan(np.radians(d_o)) - TROCHA_DEL
    return np.degrees(np.arctan(BATALLA / r)) if r > 0 else 90.0

def ackermann(rack, tr0, delta_ref=DELTA_REF, s_max=S_RACK_MAX):
    """% de Ackermann medido con la rueda exterior a delta_ref grados.
    100% = la rueda interior gira exactamente lo que pide la geometría de giro."""
    ss, out, inn = curva_giro(rack, tr0, s_max)
    if len(out) < 5 or out.max() < delta_ref or not np.all(np.diff(out) > -1e-6):
        return None, out, inn, ss
    d_o = delta_ref
    d_i = float(np.interp(d_o, out, inn))
    d_i_ideal = inner_ideal(d_o)
    return (d_i - d_o) / (d_i_ideal - d_o) * 100.0, out, inn, ss

# ============================================================================
# 3. BUMP STEER con una cremallera candidata (mismo método que la suspensión)
# ============================================================================
def bump_steer(rack, tr0):
    """Repite el barrido 3D de suspension_delantera.py con otra cremallera."""
    d_kp = np.linalg.norm(UBJ - LBJ)
    d_lt = np.linalg.norm(tr0 - LBJ)
    d_ut = np.linalg.norm(tr0 - UBJ)
    d_tr = np.linalg.norm(tr0 - rack)
    M0 = np.linalg.inv(sd.base(LBJ, UBJ, tr0))
    cW = M0 @ (sd.W0 - LBJ)
    cS = M0 @ (sd.S0 - LBJ)
    x0 = np.array([0.0, *tr0])
    ys, toes = [], []
    for thL in np.linspace(-0.30, 0.30, 49):
        lbj = sd.rot_eje(sd.LA1, sd.LA2, thL, LBJ)
        def eqs(x):
            ubj = sd.rot_eje(sd.UA1, sd.UA2, x[0], UBJ)
            tr = np.array(x[1:4])
            return [np.linalg.norm(ubj - lbj) - d_kp,
                    np.linalg.norm(tr - lbj) - d_lt,
                    np.linalg.norm(tr - ubj) - d_ut,
                    np.linalg.norm(tr - rack) - d_tr]
        x0 = fsolve(eqs, x0, full_output=False)
        ubj = sd.rot_eje(sd.UA1, sd.UA2, x0[0], UBJ)
        tr = np.array(x0[1:4])
        M = sd.base(lbj, ubj, tr)
        W = lbj + M @ cW
        a = (lbj + M @ cS - W) / 0.10
        f = np.cross(np.array([0.0, 1.0, 0.0]), a)
        ys.append(W[1]); toes.append(np.degrees(np.arctan2(-f[2], f[0])))
    ys = (np.array(ys) - sd.W0[1]) * 1000
    toes = np.array(toes)
    sel = np.abs(ys) <= 50
    if sel.sum() < 3:
        return 99.0, ys, toes
    return float(np.max(np.abs(np.gradient(toes, ys)[sel])) * 25), ys, toes

# ============================================================================
# 4. DIAGNÓSTICO DE LA GEOMETRÍA ACTUAL
# ============================================================================
ack0, out0, inn0, ss0 = ackermann(RACK0, TR0)
bs0, _, _ = bump_steer(RACK0, TR0)

# ángulo del brazo de mangueta en vista superior (kingpin → terminal)
t_kp = (TR0[1] - LBJ[1]) / (UBJ[1] - LBJ[1])
KP_TR = LBJ + t_kp * (UBJ - LBJ)               # punto del kingpin a la altura del terminal
brazo_vec = TR0 - KP_TR
L_BRAZO = float(np.hypot(brazo_vec[0], brazo_vec[2]))
ANG_BRAZO = np.degrees(np.arctan2(-brazo_vec[2], -brazo_vec[0]))   # + = hacia afuera
# ángulo que pediría el Ackermann geométrico puro (apuntar al centro del eje trasero)
ANG_IDEAL = np.degrees(np.arctan2(KP_TR[2], BATALLA))

# ============================================================================
# 5. BARRIDO DE LA CREMALLERA (sin tocar la mangueta del donante)
# ============================================================================
# Esto es lo primero que hay que probar porque NO CUESTA PIEZAS: solo cambia dónde
# se atornilla la cremallera al mamparo. La altura (y) no se toca — es la que fija
# el bump steer y ±5 mm lo duplican.
XS = np.round(np.arange(0.28, 0.531, 0.01), 3)
ZS = np.round(np.arange(0.40, 0.621, 0.01), 3)
malla = np.full((len(ZS), len(XS)), np.nan)
rack_cands = []
for i, z in enumerate(ZS):
    for j, x in enumerate(XS):
        rack = np.array([x, RACK0[1], z])
        try:
            p, out, inn, ss = ackermann(rack, TR0)
        except Exception:
            continue
        if p is None:
            continue
        malla[i, j] = p
        rack_cands.append(dict(x=x, z=z, ack=p, rack=rack, lock=float(out[-1])))
ack_max_rack = float(np.nanmax(malla)) if np.any(~np.isnan(malla)) else float("nan")

# Entre los que dan el Ackermann objetivo, se verifica el bump steer (barrido 3D
# completo) y se prefiere el que menos mueve la cremallera de donde ya estaba.
# No se busca "el que dé 85%" sino el COMPROMISO: para cada posición candidata se
# mide el bump steer real (barrido 3D completo) y se arma la frontera Ackermann vs
# bump steer. Apurar el Ackermann hasta el tope de bump steer sería mal negocio.
utiles = [c for c in rack_cands if 45 <= c["ack"] <= 150 and c["lock"] >= 24]
utiles.sort(key=lambda c: (abs(c["x"] - RACK0[0]) + abs(c["z"] - RACK0[2])))
for c in utiles[:140]:
    c["bs"], _, _ = bump_steer(c["rack"], TR0)

evaluados = [c for c in utiles if "bs" in c]

def mejor_bajo(pool, tope):
    """Bajo el tope de bump steer, el más cercano al Ackermann objetivo. No el de
    MÁS Ackermann: pasarse de 100% tampoco sirve — la rueda interior giraría más de
    lo que pide el giro y volvería a pelear, ahora al revés."""
    ok = [c for c in pool if c["bs"] <= tope]
    return min(ok, key=lambda c: abs(c["ack"] - ACK_OBJ)) if ok else None

# Refinamiento local: la malla gruesa de 10 mm salta el objetivo, así que se afina
# a 4 mm alrededor de la mejor posición encontrada.
grueso = mejor_bajo(evaluados, BS_PREF) or mejor_bajo(evaluados, BS_MAX)
if grueso is not None:
    for x in np.round(np.arange(grueso["x"] - 0.024, grueso["x"] + 0.0241, 0.004), 4):
        for z in np.round(np.arange(grueso["z"] - 0.024, grueso["z"] + 0.0241, 0.004), 4):
            rack = np.array([x, RACK0[1], z])
            try:
                p, out, _, _ = ackermann(rack, TR0)
            except Exception:
                continue
            if p is None or out[-1] < 24 or not (40 <= p <= 160):
                continue
            c = dict(x=float(x), z=float(z), ack=p, rack=rack, lock=float(out[-1]))
            c["bs"], _, _ = bump_steer(rack, TR0)
            evaluados.append(c)

# frontera de Pareto: los que nadie domina en las dos cosas a la vez
pareto = [c for c in evaluados
          if not any(o["bs"] <= c["bs"] and abs(o["ack"] - ACK_OBJ) <= abs(c["ack"] - ACK_OBJ)
                     and o is not c for o in evaluados)]
pareto.sort(key=lambda c: c["bs"])

sol_rack = mejor_bajo(evaluados, BS_PREF) or mejor_bajo(evaluados, BS_MAX)
rack_ok = pareto

# ============================================================================
# 6. PLAN B: brazo de dirección fabricado (solo si la cremallera no basta)
# ============================================================================
def tr_desde_angulo(ang_deg, largo=None):
    """Terminal de dirección a 'ang_deg' respecto del eje longitudinal
    (+ = hacia afuera del carro)."""
    L = L_BRAZO if largo is None else largo
    a = np.radians(ang_deg)
    return np.array([KP_TR[0] - L * np.cos(a), TR0[1], KP_TR[2] + L * np.sin(a)])

sol_brazo = None
if sol_rack is None:
    cands = []
    for ang in np.arange(-10.0, 26.1, 1.0):
        tr = tr_desde_angulo(ang)
        for x in np.round(np.arange(0.30, 0.481, 0.02), 3):
            rack = np.array([x, RACK0[1], RACK0[2]])
            try:
                p, out, _, _ = ackermann(rack, tr)
            except Exception:
                continue
            if p is None or out[-1] < 25:
                continue
            cands.append(dict(ang=ang, x=x, ack=p, tr=tr, rack=rack))
    cands.sort(key=lambda c: abs(c["ack"] - ACK_OBJ))
    for c in cands[:14]:
        c["bs"], _, _ = bump_steer(c["rack"], c["tr"])
        if c["bs"] <= BS_MAX and sol_brazo is None:
            sol_brazo = c

if sol_rack is not None:
    elegido, TR_N, RACK_N = sol_rack, TR0, sol_rack["rack"]
    MODO = "cremallera"
else:
    elegido, TR_N, RACK_N = sol_brazo, sol_brazo["tr"], sol_brazo["rack"]
    MODO = "brazo"

ack_n, out_n, inn_n, ss_n = ackermann(RACK_N, TR_N)
bs_n, ys_n, toes_n = bump_steer(RACK_N, TR_N)

# ============================================================================
# 7. RELACIÓN, TOPES Y CÍRCULO DE GIRO
# ============================================================================
# El tope útil no es el de la cremallera sino el ángulo interior sensato: más de 40°
# ya no cabe dentro del rin ni entre el brazo inferior y la llanta.
INN_MAX_UTIL = 40.0
def topes_y_giro(rack, tr0):
    """Tope útil (lo limita la rueda interior, que es la que pega con el brazo o el
    rin), relación, y diámetro de giro. El radio del círculo lo fija la rueda
    exterior: R = batalla / sen(ángulo exterior)."""
    ss, out, inn = curva_giro(rack, tr0, S_RACK_MAX, 120)
    k = int(np.argmax(inn >= INN_MAX_UTIL)) if np.any(inn >= INN_MAX_UTIL) else len(inn) - 1
    s_u, d_o, d_i = float(ss[k]), float(out[k]), float(inn[k])
    vueltas = 2 * s_u / P_RACK
    ratio = (vueltas * 360.0) / (d_o + d_i)
    diam = 2 * BATALLA / np.sin(np.radians(d_o)) + sd.ANCHO_LLANTA
    return s_u, d_o, d_i, vueltas, ratio, diam

S_USADA, D_OUT_MAX, D_INN_MAX, VUELTAS, RATIO, DIAM_GIRO = topes_y_giro(RACK_N, TR_N)
S_USADA_0, D_OUT_0, D_INN_0, VUELTAS_0, RATIO_0, DIAM_GIRO_0 = topes_y_giro(RACK0, TR0)

# círculo de giro con el ángulo exterior máximo
# ============================================================================
# 8. ESFUERZO EN EL VOLANTE
# ============================================================================
W_RUEDA = MASA * DIST_DEL / 2 * G                 # N por rueda delantera
# Par de pivotamiento parado (Taborek): T = mu·W^1.5 / sqrt(3·p)
T_PIVOT = MU_PISO * W_RUEDA**1.5 / np.sqrt(3 * P_LLANTA)
F_TIE = T_PIVOT / L_BRAZO                          # N en cada tie rod
F_RACK = 2 * F_TIE                                 # ambas ruedas empujan la cremallera
T_VOL = F_RACK * P_RACK / (2 * np.pi)
F_ARO = T_VOL / (D_VOLANTE / 2)
# rodando, el par es ~1/6 del de parado (no hay que torcer la huella en seco)
F_ARO_RODANDO = F_ARO / 6

# ============================================================================
# 9. INFORME
# ============================================================================
out_md = os.path.join(HERE, "resultados-direccion.md")
with open(out_md, "w", encoding="utf-8") as f:
    f.write("# Dirección — Ackermann, relación, esfuerzo y círculo de giro\n\n")
    f.write("Cremallera manual de compacto, sin servo. Generado por `direccion.py`, que importa "
            "la geometría de `suspension_delantera.py` para que no haya dos verdades.\n\n")
    f.write("**Método:** al girar el volante con la suspensión quieta, las rótulas no se mueven "
            "— la mangueta solo rota alrededor del eje de kingpin. Eso deja una sola incógnita "
            "(el ángulo de rotación) con una sola ecuación (el tie rod conserva su largo), y se "
            "resuelve exacto para las dos ruedas. Nada de fórmulas aproximadas de Ackermann.\n\n")

    f.write("## 1. Qué Ackermann trae la geometría heredada\n\n")
    f.write("Los puntos duros venían afinados para camber, caster y bump steer, pero el "
            "Ackermann nunca se había medido. Medido ahora, con la rueda exterior a "
            f"{DELTA_REF:.0f}°:\n\n")
    f.write(f"| | Valor |\n|---|---|\n")
    f.write(f"| Largo del brazo de mangueta (vista superior) | {L_BRAZO*1000:.0f} mm |\n")
    f.write(f"| **Ackermann heredado** | **{ack0:+.0f}%** |\n")
    f.write(f"| Bump steer heredado | {bs0:.3f}°/25 mm |\n\n")
    f.write("**+42% no es un desastre, pero se queda corto para un carro que estaciona.** "
            "Ackermann por debajo de 100% significa que la rueda interior gira menos de lo que "
            "pide el giro, así que las dos llantas van algo peleadas en maniobra lenta: "
            "chirrían, se comen los hombros y el volante se siente pegajoso al dar vuelta en "
            "una esquina. En pista se usa a propósito — a alto ángulo de deriva la rueda "
            "interior quiere menos ángulo — pero este carro es de calle y terreno privado, "
            f"donde manda el estacionamiento. Objetivo: **{ACK_OBJ:.0f}%**.\n\n")
    f.write("**Una aclaración que vale la pena, porque yo mismo me equivadué al empezar.** La "
            "regla de manual dice que el brazo de mangueta debe apuntar al centro del eje "
            "trasero. Eso vale para un varillaje **trapezoidal**, donde una sola barra une los "
            "dos brazos. Con **cremallera** no aplica: el Ackermann depende también de dónde "
            "está la cremallera y de qué tan largo es el tie rod, porque el varillaje es otro. "
            f"Por eso el brazo heredado apunta {abs(ANG_BRAZO):.0f}° hacia adentro (la regla "
            f"del trapecio pediría {ANG_IDEAL:.0f}° hacia afuera) y aun así el Ackermann sale "
            "positivo. Aquí todo se midió resolviendo el varillaje real, no aplicando la regla.\n\n")

    f.write("## 2. La corrección no cuesta ni una pieza\n\n")
    f.write("Como el Ackermann de una cremallera depende de dónde está la cremallera, lo "
            "primero que hay que probar es **moverla** — que es gratis, porque solo cambia "
            "dónde se atornilla al mamparo. Barrido de su posición longitudinal y su ancho "
            f"({XS[0]*1000:.0f}–{XS[-1]*1000:.0f} mm × {ZS[0]*1000:.0f}–{ZS[-1]*1000:.0f} mm, "
            f"{malla.size} posiciones), con la mangueta del donante **intacta**:\n\n")
    f.write(f"- Rango de Ackermann alcanzable moviendo solo la cremallera: hasta "
            f"**{ack_max_rack:+.0f}%**.\n")
    f.write(f"- **La altura (y = {RACK0[1]*1000:.0f} mm) no se toca**: es la que fija el bump "
            "steer y ±5 mm lo duplican.\n\n")
    if MODO == "cremallera":
        f.write("Alcanza de sobra. **No hay que tocar la mangueta ni fabricar ningún brazo.**\n\n")
        f.write("Pero subir el Ackermann no sale gratis: mover la cremallera cambia el largo "
                "del tie rod, y con él qué tan bien sigue el arco de los brazos. Así que no se "
                "busca \"el que dé 85%\" sino el **compromiso**. Cada posición candidata se "
                "verificó re-corriendo el barrido 3D completo de bump steer; ésta es la "
                "frontera de lo alcanzable (ninguna de estas es peor que otra en las dos cosas "
                "a la vez):\n\n")
        f.write("| Cremallera x | Cremallera z | Ackermann | Bump steer | |\n|---|---|---|---|---|\n")
        for c in rack_ok[:10]:
            marca = ("✓ elegida" if c is elegido else
                     "ok" if c["bs"] <= BS_PREF else
                     "más Ackermann, peor bump steer")
            f.write(f"| {c['x']*1000:.0f} mm | {c['z']*1000:.0f} mm | {c['ack']:+.0f}% | "
                    f"{c['bs']:.3f}°/25mm | {marca} |\n")
        f.write(f"\n**Criterio: el bump steer manda.** Uno hace que el carro se dirija solo al "
                f"pasar un tope; el otro solo desgasta llanta al estacionar. Así que se toma el "
                f"mejor Ackermann que quepa bajo **{BS_PREF:.3f}°/25 mm**, en vez de apurar el "
                f"Ackermann hasta el tope duro de {BS_MAX:.2f}.\n\n")
        f.write(f"**Elegida: cremallera en x = {RACK_N[0]*1000:.0f} mm, z = "
                f"{RACK_N[2]*1000:.0f} mm** (antes {RACK0[0]*1000:.0f} / "
                f"{RACK0[2]*1000:.0f}). Se mueve "
                f"{abs(RACK_N[0]-RACK0[0])*1000:.0f} mm en largo y "
                f"{abs(RACK_N[2]-RACK0[2])*1000:.0f} mm en ancho — nada más que la posición de "
                "sus dos ménsulas al mamparo.\n\n")
    else:
        f.write("No alcanza con la mangueta del donante: hay que fabricar un brazo de "
                f"dirección de {L_BRAZO*1000:.0f} mm a {elegido['ang']:+.0f}°, en acero "
                "cortado en láser.\n\n")
    f.write("| | Heredado | Corregido |\n|---|---|---|\n")
    f.write(f"| Ackermann | {ack0:+.0f}% | **{ack_n:+.0f}%** |\n")
    f.write(f"| Bump steer | {bs0:.3f}°/25mm | **{bs_n:.3f}°/25mm** |\n\n")
    f.write("| Punto duro | x | y | z |\n|---|---|---|---|\n")
    f.write(f"| Terminal de dirección (sin cambio) | {TR_N[0]*1000:.0f} | "
            f"{TR_N[1]*1000:.0f} | {TR_N[2]*1000:.0f} |\n")
    f.write(f"| **Extremo de cremallera (nuevo)** | **{RACK_N[0]*1000:.0f}** | "
            f"{RACK_N[1]*1000:.0f} | **{RACK_N[2]*1000:.0f}** |\n")
    f.write(f"| Tie rod (centro a centro) | {np.linalg.norm(TR_N-RACK_N)*1000:.0f} mm | | |\n\n")
    if bs_n < bs0 * 0.9:
        f.write(f"**El bump steer no solo se conserva: mejora**, de {bs0:.3f} a "
                f"{bs_n:.3f}°/25 mm. Al mover la cremallera cambia el largo del tie rod, y "
                "resulta que hay largos que siguen mejor el arco de los brazos. No era el "
                "objetivo — salió de buscar el compromiso en vez de apurar el Ackermann — pero "
                "es la confirmación de que valía la pena re-correr la cinemática 3D de cada "
                "candidato en vez de suponer que mover la cremallera es inocuo.\n\n")
    elif bs_n > bs0 * 1.15:
        f.write(f"**El bump steer empeora** de {bs0:.3f} a {bs_n:.3f}°/25 mm. Sigue por debajo "
                f"del tope de {BS_MAX:.2f}, pero no es gratis: mover la cremallera cambia el "
                "largo del tie rod y con él qué tan bien sigue el arco de los brazos.\n\n")
    else:
        f.write(f"El bump steer se conserva ({bs0:.3f} → {bs_n:.3f}°/25 mm), que era la "
                "condición para poder mover la cremallera.\n\n")
    f.write(f"**La altura de la cremallera ({RACK_N[1]*1000:.0f} mm) no se toca**: ±5 mm "
            "duplican el bump steer. Montarla con barrenos ovalados y calzas para afinar en el "
            "carro, como ya decía la suspensión delantera.\n\n")

    f.write("## 3. Relación, topes y círculo de giro\n\n")
    f.write(f"El tope no lo pone la cremallera sino la **rueda interior**, que es la que pega "
            f"con el brazo inferior o con el interior del rin. Se limita a {INN_MAX_UTIL:.0f}°.\n\n")
    f.write("| Parámetro | Heredado | Corregido |\n|---|---|---|\n")
    f.write(f"| Carrera de cremallera usada | ±{S_USADA_0*1000:.0f} mm | "
            f"±{S_USADA*1000:.0f} mm |\n")
    f.write(f"| Ángulo rueda exterior | {D_OUT_0:.1f}° | {D_OUT_MAX:.1f}° |\n")
    f.write(f"| Ángulo rueda interior | {D_INN_0:.1f}° | {D_INN_MAX:.1f}° |\n")
    f.write(f"| Vueltas de tope a tope | {VUELTAS_0:.1f} | **{VUELTAS:.1f}** |\n")
    f.write(f"| Relación total | {RATIO_0:.0f}:1 | **{RATIO:.0f}:1** |\n")
    f.write(f"| Diámetro de giro | {DIAM_GIRO_0:.1f} m | **{DIAM_GIRO:.1f} m** |\n\n")
    if DIAM_GIRO > DIAM_GIRO_0 + 0.2:
        f.write(f"**El Ackermann alto se paga con círculo de giro.** Con más Ackermann la rueda "
                f"interior gira más para el mismo ángulo exterior, así que llega antes a su "
                f"tope de {INN_MAX_UTIL:.0f}° y el exterior se queda en {D_OUT_MAX:.1f}° en vez "
                f"de {D_OUT_0:.1f}°. El círculo pasa de {DIAM_GIRO_0:.1f} a {DIAM_GIRO:.1f} m. "
                "Es un intercambio real, no un defecto: se gana que las llantas no peleen en "
                "maniobra lenta y se pierde algo de radio. Si al armarlo resulta que la rueda "
                f"interior sí libra más de {INN_MAX_UTIL:.0f}°, se sube el tope y se recupera "
                "el radio — por eso hay que medirlo en el carro (§5).\n\n")
    f.write(f"{VUELTAS:.1f} vueltas y {RATIO:.0f}:1 es relación directa de carro deportivo "
            "ligero (un compacto con servo anda en 3.2 vueltas y 16-18:1). Directo se siente "
            "mejor y además es lo único que se puede hacer sin servo: más desmultiplicación "
            "aligeraría el volante pero habría que dar más vueltas.\n\n")

    f.write("## 4. Esfuerzo en el volante (sin servo)\n\n")
    f.write("El caso duro es girar **parado en seco**, que es cuando hay que torcer la huella "
            "de la llanta sobre el piso. Fórmula de Taborek para el par de pivotamiento:\n\n")
    f.write(f"| | Valor |\n|---|---|\n")
    f.write(f"| Carga por rueda delantera | {W_RUEDA/G:.0f} kg |\n")
    f.write(f"| Par de pivotamiento por rueda | {T_PIVOT:.0f} N·m |\n")
    f.write(f"| Fuerza en cada tie rod | {F_TIE:.0f} N |\n")
    f.write(f"| Par en el volante | {T_VOL:.1f} N·m |\n")
    f.write(f"| **Fuerza en el aro (Ø{D_VOLANTE*1000:.0f} mm), parado** | "
            f"**{F_ARO:.0f} N** |\n")
    f.write(f"| Fuerza en el aro rodando | ~{F_ARO_RODANDO:.0f} N |\n\n")
    f.write(f"{F_ARO:.0f} N con las dos manos es un volante firme pero perfectamente manejable "
            "— comparable a un carro chico de los 80 sin servo. Ayudan tres cosas que ya están "
            f"en la geometría: el eje delantero solo carga {DIST_DEL*100:.0f}% del peso (los "
            "motores van atrás), el radio de pivotamiento es chico, y la llanta es angosta. "
            "**Y casi nunca se gira totalmente parado**: rodando aunque sea a paso de hombre "
            f"baja a ~{F_ARO_RODANDO:.0f} N.\n\n")
    f.write(f"Si al armarlo se siente pesado, la salida es subir la presión de las llantas o "
            f"alargar el brazo de dirección — pero alargarlo baja el ángulo de giro máximo y "
            "sube el diámetro de vuelta. Es un intercambio, no una mejora gratis.\n\n")

    f.write("## 5. Columna y montaje\n\n")
    f.write("- Columna de compacto de deshuesadero con **2 crucetas (junta universal)**: una en "
            "el volante y otra en el piñón. Los ángulos de las crucetas deben ser parecidos "
            "entre sí y **en fase**, si no la dirección se siente que \"pulsa\" al girar.\n")
    f.write("- **Junta de seguridad plegable o columna colapsable del donante**: en un impacto "
            "frontal la columna no debe empujar la barra del volante contra el pecho.\n")
    f.write("- La cremallera va atornillada al mamparo delantero con **barrenos ovalados y "
            "calzas** para afinar altura en el carro (§3).\n")
    f.write("- Topes de giro: verificar en el carro que a tope la llanta no pegue con el brazo "
            "inferior ni con el interior del rin, ANTES de confiar en la carrera de "
            f"±{S_RACK_MAX*1000:.0f} mm de la cremallera. Si pega, se limita con topes en la "
            "cremallera y se re-corre este script.\n\n")

    f.write("## 6. Lista de compra de esta sección\n\n")
    f.write("- 1 × cremallera manual de compacto (donante) — medir su carrera real y su avance "
            f"por vuelta; aquí se supuso ±{S_RACK_MAX*1000:.0f} mm y {P_RACK*1000:.0f} mm/vuelta\n")
    f.write("- 1 × columna con 2 crucetas + soporte, preferentemente colapsable\n")
    f.write(f"- 1 × volante Ø{D_VOLANTE*1000:.0f} mm con maza\n")
    f.write("- 2 × terminal de dirección (rótula) + 2 × rótula axial de cremallera\n")
    if MODO == "cremallera":
        f.write("- 2 × ménsula de cremallera al mamparo, corte láser, con barrenos ovalados "
                f"(posición nueva: x = {RACK_N[0]*1000:.0f} mm, z = ±{RACK_N[2]*1000:.0f} mm)\n")
        f.write("- **Brazo de dirección: ninguno.** El de la mangueta del donante se queda "
                "como viene.\n")
    else:
        f.write(f"- 2 × **brazo de dirección fabricado**, acero, corte láser, largo "
                f"{L_BRAZO*1000:.0f} mm a {elegido['ang']:+.0f}°\n")
    f.write("- Tubo roscado derecha/izquierda para el tie rod (permite ajustar convergencia sin "
            "desmontar)\n")

# ============================================================================
# 10. GRÁFICA
# ============================================================================
fig, axs = plt.subplots(2, 2, figsize=(13, 8.8), facecolor="#0d1117")
for ax in axs.flat:
    ax.set_facecolor("#0d1117"); ax.grid(color="#21262d", lw=0.6)
    ax.tick_params(colors="#8b949e", labelsize=8.5)
    for sp in ax.spines.values(): sp.set_color("#30363d")

# (1) vista superior: brazo heredado vs corregido
ax = axs[0, 0]
ax.plot([KP_TR[0]*1000], [KP_TR[2]*1000], marker="o", color="#38bdf8", ms=8)
ax.annotate("kingpin", (KP_TR[0]*1000, KP_TR[2]*1000), textcoords="offset points",
            xytext=(8, -12), color="#38bdf8", fontsize=8)
ax.plot([KP_TR[0]*1000, TR0[0]*1000], [KP_TR[2]*1000, TR0[2]*1000],
        color="#e6edf3", lw=3, label=f"brazo de mangueta ({L_BRAZO*1000:.0f} mm)")
ax.plot([RACK0[0]*1000, TR0[0]*1000], [RACK0[2]*1000, TR0[2]*1000],
        color="#f87171", lw=2, ls=":", label=f"tie rod heredado ({ack0:+.0f}%)")
ax.plot([RACK_N[0]*1000, TR_N[0]*1000], [RACK_N[2]*1000, TR_N[2]*1000],
        color="#4ade80", lw=2, label=f"tie rod nuevo ({ack_n:+.0f}%)")
ax.plot([RACK0[0]*1000], [RACK0[2]*1000], marker="o", color="#f87171", ms=7)
ax.plot([RACK_N[0]*1000], [RACK_N[2]*1000], marker="o", color="#4ade80", ms=7)
ax.plot([sd.W0[0]*1000], [sd.W0[2]*1000], marker="s", color="#8b949e", ms=7)
ax.annotate("rueda", (sd.W0[0]*1000, sd.W0[2]*1000), textcoords="offset points",
            xytext=(8, 6), color="#8b949e", fontsize=8)
ax.set_xlim(250, 850); ax.set_ylim(400, 820)
ax.invert_yaxis(); ax.set_aspect("equal")
ax.set_title("Vista superior (mm): mover la cremallera\ncambia el Ackermann sin tocar la mangueta",
             color="#e6edf3", fontsize=10)
ax.legend(facecolor="#0d1117", edgecolor="#30363d", labelcolor="#e6edf3", fontsize=8)

# (2) ángulo interior vs exterior
ax = axs[0, 1]
d_o = np.linspace(1, max(out_n.max(), out0.max()), 100)
r_ideal = BATALLA / np.tan(np.radians(d_o)) - TROCHA_DEL
d_i_ideal = np.degrees(np.arctan(BATALLA / np.maximum(r_ideal, 1e-6)))
ax.plot(d_o, d_i_ideal, color="#8b949e", lw=1.6, ls="--", label="Ackermann 100%")
ax.plot(d_o, d_o, color="#3a4a5a", lw=1.2, ls=":", label="paralelo (0%)")
ax.plot(out0, inn0, color="#f87171", lw=2.2, label=f"heredado ({ack0:+.0f}%)")
ax.plot(out_n, inn_n, color="#4ade80", lw=2.2, label=f"corregido ({ack_n:+.0f}%)")
ax.set_xlim(0, 35); ax.set_ylim(0, 45)
ax.set_title("Ángulo de la rueda interior vs la exterior", color="#e6edf3", fontsize=10)
ax.set_xlabel("rueda exterior (°)", color="#8b949e", fontsize=9)
ax.set_ylabel("rueda interior (°)", color="#8b949e", fontsize=9)
ax.legend(facecolor="#0d1117", edgecolor="#30363d", labelcolor="#e6edf3", fontsize=8)

# (3) bump steer antes y después
ax = axs[1, 0]
_, ys0, toes0 = bump_steer(RACK0, TR0)
ax.plot(ys0, (toes0 - np.interp(0, ys0, toes0)) * 60, color="#f87171", lw=2,
        label=f"heredado ({bs0:.3f}°/25mm)")
ax.plot(ys_n, (toes_n - np.interp(0, ys_n, toes_n)) * 60, color="#4ade80", lw=2,
        label=f"corregido ({bs_n:.3f}°/25mm)")
ax.axvline(0, color="#30363d", lw=1)
ax.set_title(f"Bump steer: {'baja' if bs_n < bs0 else 'sube'} de {bs0:.3f} a "
             f"{bs_n:.3f}°/25mm\n(tope {BS_MAX:.2f})", color="#e6edf3", fontsize=10)
ax.set_xlabel("recorrido de rueda (mm)", color="#8b949e", fontsize=9)
ax.set_ylabel("convergencia (minutos de arco)", color="#8b949e", fontsize=9)
ax.legend(facecolor="#0d1117", edgecolor="#30363d", labelcolor="#e6edf3", fontsize=8)

# (4) esfuerzo en el volante vs presión de llanta
ax = axs[1, 1]
pp = np.linspace(1.6e5, 3.0e5, 60)
tt = MU_PISO * W_RUEDA**1.5 / np.sqrt(3 * pp)
ff = (2 * tt / L_BRAZO) * P_RACK / (2 * np.pi) / (D_VOLANTE / 2)
ax.plot(pp / 1e5, ff, color="#f97316", lw=2.2, label="parado, en seco")
ax.plot(pp / 1e5, ff / 6, color="#38bdf8", lw=2.2, label="rodando")
ax.plot(P_LLANTA / 1e5, F_ARO, marker="*", ms=16, color="#4ade80", zorder=5)
ax.set_title("Fuerza en el aro del volante", color="#e6edf3", fontsize=10)
ax.set_xlabel("presión de llanta (bar)", color="#8b949e", fontsize=9)
ax.set_ylabel("N", color="#8b949e", fontsize=9)
ax.legend(facecolor="#0d1117", edgecolor="#30363d", labelcolor="#e6edf3", fontsize=8)

fig.suptitle(f"Dirección — cremallera manual · Ackermann {ack0:+.0f}% → {ack_n:+.0f}% "
             "moviendo solo la cremallera, sin tocar la mangueta",
             color="#e6edf3", fontsize=12)
fig.tight_layout()
out_png = os.path.join(HERE, "direccion.png")
fig.savefig(out_png, dpi=150, facecolor="#0d1117", bbox_inches="tight")

print(f"\n--- direccion ---")
print(f"brazo heredado: largo {L_BRAZO*1000:.0f} mm, angulo {ANG_BRAZO:+.1f}° "
      f"(ideal {ANG_IDEAL:+.1f}°) -> Ackermann {ack0:+.0f}%, bump steer {bs0:.3f}")
print(f"solo moviendo cremallera: Ackermann max {ack_max_rack:+.0f}%")
print(f"solucion por {MODO}: cremallera x {RACK_N[0]*1000:.0f} z {RACK_N[2]*1000:.0f} mm "
      f"-> Ackermann {ack_n:+.0f}%, bump steer {bs_n:.3f}")
print(f"topes: ext {D_OUT_MAX:.1f}° int {D_INN_MAX:.1f}°  {VUELTAS:.1f} vueltas  "
      f"ratio {RATIO:.0f}:1  diametro de giro {DIAM_GIRO:.1f} m")
print(f"esfuerzo: par pivot {T_PIVOT:.0f} N.m -> aro {F_ARO:.0f} N parado, "
      f"{F_ARO_RODANDO:.0f} N rodando")
print(f"OK  informe: {out_md}\nOK  grafica: {out_png}")
