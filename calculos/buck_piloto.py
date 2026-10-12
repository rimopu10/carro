# calculos/buck_piloto.py
# -*- coding: utf-8 -*-
"""
Maqueta de asiento (seating buck) del piloto: cuerpo humano real y las métricas que deciden si la
cabina funciona. Reemplaza al maniquí de carroceria.py (cadera->hombro 0.41 m; un adulto de 1.75 m
tiene ~0.51).

Plano (x, y): x crece hacia ATRÁS, y arriba. Todo en metros.

    python calculos/buck_piloto.py        # tabla de la postura nominal y del recorrido
"""
import numpy as np

# --- hombre p50, 1.75 m (antropometría estándar) ---
ESTATURA_REF = 1.75
TRONCO = 0.51          # cadera -> hombro
HOMBRO_OJO = 0.19      # hombro -> ojo, vertical
OJO_CORONILLA = 0.12
OJO_NUCA = 0.10        # ojo -> parte de atrás de la cabeza, horizontal
MUSLO = 0.43           # cadera -> rodilla
PIERNA = 0.41          # rodilla -> tobillo
Y_SUELA = 0.18         # suela sobre el tablero del piso (tubo del piso y=0.16 + radio)
TOBILLO_ALTO = 0.08
PIE_BOLA = 0.15        # tobillo -> bola del pie (hacia adelante)
ESPALDA_CUBETA = 0.13  # del hombro a la cara trasera de la cubeta: 9 cm de espalda + 4 cm de cubeta

# --- carrocería de Tripo medida (cara INTERIOR del techo, z=0.31) ---
TECHO_INT = [(1.45, 0.998), (1.60, 1.025), (1.75, 1.045), (1.90, 1.053), (2.00, 1.048), (2.10, 1.039)]
FORRO = 0.020
ARCO_X_FRENTE = 2.02 - 0.0254      # cara delantera del arco (RED 50.8)
CABECERA = (1.45, 0.949)           # eje de la cabecera sobre el piloto (x, y), a z=0.31 (hdr 0.94 -> sp_f 0.965)
CABECERA_R = 0.0286                # cabecera RED 57.2 (radio real; con 25.4 se sobrestimaba el ángulo)


def limite_techo(x):
    xs, ys = zip(*TECHO_INT)
    return float(np.interp(x, xs, ys)) - FORRO


def postura(hx, hy, recline_deg, estatura=ESTATURA_REF, muslo_deg=10.0):
    """Cuerpo sentado con la cadera en (hx, hy). Segmentos escalados por estatura/1.75."""
    k = estatura / ESTATURA_REF
    th, al = np.radians(recline_deg), np.radians(muslo_deg)
    cadera = np.array([hx, hy])
    hombro = cadera + k * TRONCO * np.array([np.sin(th), np.cos(th)])
    ojo = hombro + np.array([-0.03, k * HOMBRO_OJO])
    coronilla = ojo + np.array([0.0, k * OJO_CORONILLA])
    nuca = ojo + np.array([OJO_NUCA, 0.0])
    rodilla = cadera + k * MUSLO * np.array([-np.cos(al), np.sin(al)])
    y_tob = Y_SUELA + TOBILLO_ALTO
    dx = np.sqrt(max((k * PIERNA) ** 2 - (rodilla[1] - y_tob) ** 2, 0.0))
    tobillo = np.array([rodilla[0] - dx, y_tob])
    bola = tobillo + np.array([-PIE_BOLA, -TOBILLO_ALTO + 0.02])
    return dict(cadera=cadera, hombro=hombro, ojo=ojo, coronilla=coronilla, nuca=nuca,
                rodilla=rodilla, tobillo=tobillo, bola=bola)


def metricas(p):
    ojo = p["ojo"]
    borde = CABECERA[1] - CABECERA_R
    return dict(
        holgura_techo=limite_techo(p["coronilla"][0]) - p["coronilla"][1],
        nuca_arco=ARCO_X_FRENTE - p["nuca"][0],
        espalda_barra=ARCO_X_FRENTE - (p["hombro"][0] + ESPALDA_CUBETA),   # espalda + cubeta vs la barra de cinturones
        cabecera_grados=float(np.degrees(np.arctan((borde - ojo[1]) / (ojo[0] - CABECERA[0])))),
        pedal_x=float(p["bola"][0]),
        ojo=(float(ojo[0]), float(ojo[1])),
    )


def capsulas(p, z=0.31):
    """Volumen que ocupa el cuerpo, como cápsulas 3D (a, b, radio) en el plano z=z. Los tubos del chasis no
    pueden pasar por ahí. Torso con holgura de respaldo de 4 cm."""
    def v(q):
        return np.array([q[0], q[1], z])
    asiento = np.array([0.0, 0.05])      # el cuerpo descansa sobre el cojín, 5 cm sobre el travesaño del piso
    centro_cabeza = p["ojo"] + np.array([0.045, -0.04])
    return [
        dict(nombre="muslo", a=v(p["cadera"] + asiento), b=v(p["rodilla"] + asiento), r=0.095),
        dict(nombre="pierna", a=v(p["rodilla"]), b=v(p["tobillo"]), r=0.08),
        dict(nombre="pie", a=v(p["tobillo"]), b=v(p["bola"]), r=0.06),
        dict(nombre="torso", a=v(p["cadera"] + asiento), b=v(p["hombro"]), r=0.15),
        dict(nombre="cabeza", a=v(centro_cabeza), b=v(centro_cabeza + np.array([0.04, 0.0])), r=0.115),
    ]


def dist_punto_capsula(P, c):
    """Distancia (m) de los puntos P (n,3) al eje de la cápsula c, menos su radio."""
    a, b = c["a"], c["b"]
    ab = b - a
    t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-12), 0.0, 1.0)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1) - c["r"]


NOMINAL = dict(hx=1.50, hy=0.26, recline=40.0)


def cadera_para_pedal(estatura, pedal_x=None, hy=None, recline=None):
    """x de la cadera con la que un conductor de esa estatura alcanza el MISMO pedal (los pedales son fijos):
    el alto se sienta más atrás, el bajo más adelante. Bisección sobre hx."""
    pedal_x = metricas(postura(NOMINAL["hx"], NOMINAL["hy"], NOMINAL["recline"]))["pedal_x"] if pedal_x is None else pedal_x
    hy = NOMINAL["hy"] if hy is None else hy
    recline = NOMINAL["recline"] if recline is None else recline
    lo, hi = 1.20, 1.90
    for _ in range(60):
        mid = (lo + hi) / 2
        if metricas(postura(mid, hy, recline, estatura=estatura))["pedal_x"] > pedal_x:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


# recorrido de la cadera en x con pedales fijos: de 1.60 m (extremo delantero) a 1.80 m (trasero). Más alto no cabe:
# a 1.85 m la espalda toca la barra de cinturones.
RIELES = (round(cadera_para_pedal(1.60), 2), round(cadera_para_pedal(1.80), 2))


if __name__ == "__main__":
    for est, hx in ((1.60, RIELES[0]), (1.75, NOMINAL["hx"]), (1.80, RIELES[1]), (1.85, round(cadera_para_pedal(1.85), 2))):
        m = metricas(postura(hx, NOMINAL["hy"], NOMINAL["recline"], estatura=est))
        print(f"{est:.2f} m, cadera x={hx:.2f}: techo {m['holgura_techo']*1000:+.0f} mm  nuca-arco {m['nuca_arco']*1000:+.0f} mm  "
              f"espalda-barra {m['espalda_barra']*1000:+.0f} mm  cabecera {m['cabecera_grados']:+.1f}°  pedal x {m['pedal_x']:.2f}")
