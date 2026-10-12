# calculos/puertas.py
# -*- coding: utf-8 -*-
"""
Puertas de gaviota: eje de bisagra, amortiguador de gas, fuerzas con la puerta abierta (caso LC7 del chasis)
y coordenadas del herraje. Lado izquierdo (z>0); el derecho es el espejo en z.

Ejes del proyecto: x hacia atrás, y arriba, z lateral. La puerta gira hacia ARRIBA y hacia afuera: rotación de
-theta (regla de la mano derecha) sobre el eje +x del riel del techo.

    python calculos/puertas.py
"""
import itertools
import numpy as np

G = 9.81
MASA_PUERTA = 10.0          # kg (piel sándwich + esqueleto Ø16 + cristal PC + herraje)
FACTOR_BACHE = 3.0          # la puerta abierta recibe 3 g al pasar un bache / un portazo
VIENTO_N = 400.0            # N laterales, en el centro de la puerta abierta
THETA_MAX = 65.0

# riel del espinazo sp_f -> sp_r (chasis), lado izquierdo: ahí van soldadas las BASES de las bisagras
A_SF = np.array([1.45, 0.965, 0.15])
A_SR = np.array([2.02, 1.01, 0.15])
# eje de giro: horizontal, a y=1.06 (dentro de la piel del techo, ~50 mm bajo su cara exterior), igual que en las
# piezas de la puerta (tripo_gaviota.py: Y_BISAGRA). Las ménsulas de la bisagra salvan los 5-9 cm entre el riel y el eje.
EJE_A0 = np.array([1.45, 1.06, 0.15])
EJE_U = np.array([1.0, 0.0, 0.0])
X_H1, X_H2 = 1.55, 1.85     # x de las 2 bisagras: flanquean el centro de masa de la puerta (x=1.70)
S_H1, S_H2 = (X_H1 - A_SF[0]) / (A_SR[0] - A_SF[0]), (X_H2 - A_SF[0]) / (A_SR[0] - A_SF[0])

CM_CERRADA = np.array([1.70, 0.72, 0.70])     # centro de masa de la puerta cerrada
BORDE_INF = np.array([1.70, 0.28, 0.90])      # punto bajo del borde de la puerta
SA = np.array([1.45, 0.949, 0.30])            # ancla del amortiguador en el chasis (cabecera, lado izq.)


def punto_riel(s):
    return A_SF + (A_SR - A_SF) * s


def giro(p, theta_deg):
    """Rota el punto p (puerta cerrada) theta grados hacia arriba/afuera sobre el eje de la bisagra."""
    a = np.radians(-theta_deg)
    q = np.asarray(p, float) - EJE_A0
    u = EJE_U
    qr = q * np.cos(a) + np.cross(u, q) * np.sin(a) + u * np.dot(u, q) * (1 - np.cos(a))
    return EJE_A0 + qr


def _fuerza_para(pd, theta, factor_peso=1.0, viento=0.0):
    """Fuerza del amortiguador (N) que anula el momento sobre el eje con la puerta a theta."""
    cm = giro(CM_CERRADA, theta)
    tau_ext = np.dot(np.cross(cm - EJE_A0, np.array([0.0, -MASA_PUERTA * G * factor_peso, viento])), EJE_U)
    p = giro(pd, theta)
    d = (p - SA) / np.linalg.norm(p - SA)           # el amortiguador EMPUJA a la puerta lejos del chasis
    lever = np.dot(np.cross(p - EJE_A0, d), EJE_U)
    return None if abs(lever) < 1e-9 else float(-tau_ext / lever)


def _disenar_ancla():
    """Busca el ancla del amortiguador en la puerta (PD, cerrada) que sostenga THETA_MAX con la MENOR fuerza,
    con carrera de 80-180 mm y longitud comprimida >= 0.20 m."""
    best, best_score = None, 1e9
    for x, y, z in itertools.product(np.arange(1.30, 1.56, 0.05), np.arange(0.55, 0.91, 0.05),
                                     np.arange(0.50, 0.91, 0.05)):
        pd = np.array([x, y, z])
        l0 = np.linalg.norm(pd - SA)
        carrera = np.linalg.norm(giro(pd, THETA_MAX) - SA) - l0
        if not (0.08 <= carrera <= 0.18) or l0 < 0.20:
            continue
        f = _fuerza_para(pd, THETA_MAX)
        if f is None or f <= 0:
            continue
        score = f                      # la geometría con más palanca pide el amortiguador más suave
        if score < best_score:
            best, best_score = pd, score
    if best is None:
        raise RuntimeError("no hay ancla de amortiguador que cumpla las restricciones")
    return best


PD = _disenar_ancla()

CATALOGO_N = (250.0, 300.0, 350.0, 400.0, 500.0)      # amortiguadores de gas de catálogo
BRAZO_MANO = 0.80                                       # m del eje a la manija (esfuerzo al abrir)


def fuerza_amortiguador(theta, factor_peso=1.0, viento=0.0):
    """Fuerza que DEBERÍA dar el amortiguador para sostener la puerta en theta (sólo diseño)."""
    return _fuerza_para(PD, theta, factor_peso, viento)


# amortiguador elegido: el más chico de catálogo con 10% de margen sobre lo que pide la puerta a THETA_MAX
FUERZA_NOMINAL = next(f for f in CATALOGO_N if f >= 1.1 * _fuerza_para(PD, THETA_MAX))


def esfuerzo_manual(theta):
    """Esfuerzo (N, en la manija) para mover la puerta con el amortiguador nominal: >0 = hay que levantarla,
    <0 = el amortiguador la levanta solo."""
    cm = giro(CM_CERRADA, theta)
    tau_g = -np.dot(np.cross(cm - EJE_A0, np.array([0.0, -MASA_PUERTA * G, 0.0])), EJE_U)
    p = giro(PD, theta)
    d = (p - SA) / np.linalg.norm(p - SA)
    tau_s = FUERZA_NOMINAL * np.dot(np.cross(p - EJE_A0, d), EJE_U)
    return float((tau_g - tau_s) / BRAZO_MANO) * -1.0


def carrera_amortiguador():
    return float(np.linalg.norm(giro(PD, THETA_MAX) - SA) - np.linalg.norm(PD - SA))


def estatica(theta, factor_peso=1.0, viento=0.0):
    """Fuerzas sobre la puerta a theta: peso+viento, amortiguador y reacción total de las bisagras."""
    cm = giro(CM_CERRADA, theta)
    p = giro(PD, theta)
    fs = _fuerza_para(PD, theta, factor_peso, viento)
    f_ext = np.array([0.0, -MASA_PUERTA * G * factor_peso, viento])
    f_amort = fs * (p - SA) / np.linalg.norm(p - SA)
    f_bis = -(f_ext + f_amort)
    punto_bisagras = np.array([(X_H1 + X_H2) / 2, EJE_A0[1], EJE_A0[2]])      # el perno está SOBRE el eje
    return dict(fuerza_amortiguador=fs,
                fuerzas_en_puerta=[(cm, f_ext), (p, f_amort), (punto_bisagras, f_bis)])


def lc7(theta=THETA_MAX):
    """Cargas sobre el CHASIS con la puerta abierta. Dict nodo -> (fx, fy, fz, mx, my, mz) en N y N·m, ambos lados.
    Bisagras: reacción repartida por la posición del centro de masa, aplicada en el PERNO (y=1.06) y trasladada al
    nodo del riel con su momento de excentricidad. Amortiguador: su fuerza nominal en el ancla de la cabecera."""
    p = giro(PD, theta)
    f_ext = np.array([0.0, -MASA_PUERTA * G * FACTOR_BACHE, VIENTO_N])
    f_amort = FUERZA_NOMINAL * (p - SA) / np.linalg.norm(p - SA)    # el exceso lo toma el tope de apertura
    f_bis = -(f_ext + f_amort)
    cm_x = giro(CM_CERRADA, theta)[0]
    w2 = float(np.clip((cm_x - X_H1) / (X_H2 - X_H1), 0.0, 1.0))
    L = {}
    for nombre, x, w in (("h1L", X_H1, 1 - w2), ("h2L", X_H2, w2)):
        f = -f_bis * w
        pin = np.array([x, EJE_A0[1], 0.15])
        nodo = np.array([x, A_SF[1] + (A_SR[1] - A_SF[1]) * (x - A_SF[0]) / (A_SR[0] - A_SF[0]), 0.15])
        L[nombre] = np.concatenate([f, np.cross(pin - nodo, f)])
    L["saL"] = np.concatenate([-f_amort, np.zeros(3)])
    out = dict(L)
    for k, v in L.items():     # espejo en z: las fuerzas cambian fz; los momentos (vectores axiales) cambian mx y my
        out[k[:-1] + "R"] = np.array([v[0], v[1], -v[2], -v[3], -v[4], v[5]])
    return out


def borde_inferior_abierto(theta):
    return giro(BORDE_INF, theta)


def herraje():
    """Coordenadas (lado izquierdo, puerta cerrada) del herraje, en metros."""
    return {
        "bisagra_1": np.array([X_H1, EJE_A0[1], 0.15]), "bisagra_2": np.array([X_H2, EJE_A0[1], 0.15]),   # pernos
        "amortiguador_chasis": SA.copy(), "amortiguador_puerta": PD.copy(),
        "cierre_techo_delantero": np.array([1.45, 0.94, 0.40]),     # esquina de la cabecera
        "cierre_estribo_delantero": np.array([1.40, 0.16, 0.59]),
        "cierre_estribo_trasero": np.array([1.90, 0.16, 0.59]),
        "cierre_trasero": np.array([2.02, 0.742, 0.492]),           # pierna del arco
    }


if __name__ == "__main__":
    print(f"ancla del amortiguador en la puerta: {np.round(PD, 3)}  carrera {carrera_amortiguador()*1000:.0f} mm")
    print(f"sostener 65° pide {fuerza_amortiguador(65.0):.0f} N -> amortiguador de catálogo {FUERZA_NOMINAL:.0f} N")
    for th in (0, 10, 30, 45, 65):
        print(f"  puerta a {th:2d}°: esfuerzo en la manija {esfuerzo_manual(th):+6.0f} N (+ = levantar)")
    print("borde inferior abierto a 65°:", np.round(borde_inferior_abierto(65.0), 3))
    for k, v in lc7().items():
        print(f"  LC7 {k}: F {np.round(v[:3], 1)} N   M {np.round(v[3:], 1)} N·m")
