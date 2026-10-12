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

# eje: el riel del espinazo sp_f -> sp_r, lado izquierdo
A_SF = np.array([1.45, 0.965, 0.15])
A_SR = np.array([2.02, 1.01, 0.15])
EJE_A0 = A_SF.copy()
EJE_U = (A_SR - A_SF) / np.linalg.norm(A_SR - A_SF)
S_H1, S_H2 = 0.12, 0.86     # estaciones de las 2 bisagras a lo largo del riel (fracción)

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
    punto_bisagras = punto_riel((S_H1 + S_H2) / 2)
    return dict(fuerza_amortiguador=fs,
                fuerzas_en_puerta=[(cm, f_ext), (p, f_amort), (punto_bisagras, f_bis)])


def lc7(theta=THETA_MAX):
    """Cargas sobre el CHASIS con la puerta abierta: reacción de las 2 bisagras (reparto por posición del centro
    de masa) y del amortiguador. Dict nodo -> fuerza (3,) en N, ambos lados."""
    # peso x3 g y viento sobre la puerta; el amortiguador empuja con su fuerza NOMINAL (el exceso lo toma el tope)
    p = giro(PD, theta)
    f_ext = np.array([0.0, -MASA_PUERTA * G * FACTOR_BACHE, VIENTO_N])
    f_amort = FUERZA_NOMINAL * (p - SA) / np.linalg.norm(p - SA)
    f_bis = -(f_ext + f_amort)
    cm_x = giro(CM_CERRADA, theta)[0]
    x1, x2 = punto_riel(S_H1)[0], punto_riel(S_H2)[0]
    w2 = float(np.clip((cm_x - x1) / (x2 - x1), 0.0, 1.0))
    L = {"h1L": -f_bis * (1 - w2), "h2L": -f_bis * w2, "saL": -f_amort}
    out = dict(L)
    for k, v in L.items():
        out[k[:-1] + "R"] = np.array([v[0], v[1], -v[2]])
    return out


def borde_inferior_abierto(theta):
    return giro(BORDE_INF, theta)


def herraje():
    """Coordenadas (lado izquierdo, puerta cerrada) del herraje, en metros."""
    return {
        "bisagra_1": punto_riel(S_H1), "bisagra_2": punto_riel(S_H2),
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
        print(f"  LC7 {k}: {np.round(v, 1)} N")
