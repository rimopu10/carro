# -*- coding: utf-8 -*-
"""
Jaula de control de la carrocería v3 — superficie de subdivisión.

Cómo se modela un carro en un estudio: NO se loftean secciones lisas (eso da jabón),
se construye una JAULA de pocos cuadriláteros cuyas aristas longitudinales son las
líneas de carácter —estribo, hombro, arista de salpicadera, base del cristal, borde
del techo— y se le aplica subdivisión Catmull-Clark con CREASE en esas aristas. El
crease es lo que hace que la luz se quiebre donde debe y el carro deje de ser una
pastilla de jabón.

Esta jaula se construye por código a partir de curvas MEDIDAS de la referencia
(ref/curvas-referencia.json, de calculos/curvas_ref.py) sobre los puntos duros del
chasis. Cada estación x es un anillo de 2·N_MEDIA-2 vértices; hay 12 anillos por
media sección, de la quilla al techo:

   0 piso centro      4 flanco            8 base del cristal (DLO)  [crease]
   1 borde del piso   5 hombro (ancho máx) 9 cristal medio
   2 quilla/estribo   6 arista salpicadera 10 borde del techo
   3 tope del faldón  7 repisa            11 techo centro

Fuera del invernadero, los anillos 8-10 se tienden sobre el cofre / la cubierta y su
crease se apaga, así que la misma jaula sirve de nariz a cola sin costuras.

Salida: cad/carro-v3-jaula.json  (vértices, caras, creases por arista, anillo y
        estación por cara, puntos duros). Lo levanta render/carro_v3.py en Blender.

Este módulo sólo usa numpy + json para que el Python de Blender lo pueda importar.
Correr suelto:  python calculos/carro3d_jaula.py   (escribe el JSON y una lámina
de verificación en calculos/carro3d-jaula.png si hay matplotlib).
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(HERE, "..")
CURVAS = json.load(open(os.path.join(RAIZ, "ref", "curvas-referencia.json"),
                        encoding="utf-8"))
CHASIS = json.load(open(os.path.join(RAIZ, "cad", "chasis.json"), encoding="utf-8"))

P = CURVAS["paquete"]
X_MORRO, X_COLA = P["x_morro"], P["x_cola"]
EJE_DEL, EJE_TRAS = P["eje_del"], P["eje_tras"]
SEMI, ALTO = P["semi"], P["alto"]
R_DEL, R_TRAS = 0.2876, 0.3005
Z_RUEDA_DEL, Z_RUEDA_TRAS = 0.750, 0.760
ANCHO_LL = 0.177
Y_PISO = 0.125                # borde inferior de la piel: 16 mm bajo el tubo más bajo
MARGEN_ARRIBA = 0.020         # piel sobre el tubo (además del radio del tubo)
MARGEN_LADO = 0.030


# ============================================================================
# 1. Interpolación monótona (PCHIP de Fritsch-Carlson). Sin scipy a propósito: esto
#    corre dentro de Blender, y Catmull-Rom se pasaría de largo en las esquinas.
# ============================================================================
def pchip(xk, yk):
    xk, yk = np.asarray(xk, float), np.asarray(yk, float)
    n = len(xk)
    h = np.diff(xk)
    d = np.diff(yk) / h
    m = np.zeros(n)
    if n == 2:
        m[:] = d[0]
    else:
        for i in range(1, n - 1):
            if d[i - 1] * d[i] <= 0:
                m[i] = 0.0
            else:
                w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
                m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
        m[0] = ((2 * h[0] + h[1]) * d[0] - h[0] * d[1]) / (h[0] + h[1])
        if np.sign(m[0]) != np.sign(d[0]):
            m[0] = 0.0
        elif np.sign(d[0]) != np.sign(d[1]) and abs(m[0]) > abs(3 * d[0]):
            m[0] = 3 * d[0]
        m[-1] = ((2 * h[-1] + h[-2]) * d[-1] - h[-1] * d[-2]) / (h[-1] + h[-2])
        if np.sign(m[-1]) != np.sign(d[-1]):
            m[-1] = 0.0
        elif np.sign(d[-1]) != np.sign(d[-2]) and abs(m[-1]) > abs(3 * d[-1]):
            m[-1] = 3 * d[-1]

    def f(x):
        x = np.asarray(x, float)
        i = np.clip(np.searchsorted(xk, x) - 1, 0, n - 2)
        t = (x - xk[i]) / h[i]
        h00 = 2 * t**3 - 3 * t**2 + 1
        h10 = t**3 - 2 * t**2 + t
        h01 = -2 * t**3 + 3 * t**2
        h11 = t**3 - t**2
        return h00 * yk[i] + h10 * h[i] * m[i] + h01 * yk[i + 1] + h11 * h[i] * m[i + 1]
    return lambda x: float(f(x)) if np.isscalar(x) else f(x)


def tabla(pares):
    return pchip([p[0] for p in pares], [p[1] for p in pares])


def medida(vista, clave):
    """Curva medida como función de x (lineal: son 900 puntos, no hace falta más)."""
    xs, ys = np.array(CURVAS[vista]["x"]), np.array(CURVAS[vista][clave])
    return lambda x: float(np.interp(x, xs, ys))


# ============================================================================
# 2. CURVAS MAESTRAS
# ============================================================================
techo_ref = medida("lateral", "techo")
piso_ref = medida("lateral", "piso")
semi_ref = medida("cenital", "semiancho")
canopy_ref = medida("cenital", "cristal")
luneta_ref = medida("cenital", "luneta")

# La piel no puede entrar al chasis: techo mínimo = tubo + radio + margen. Donde la
# lámina pide menos (cowl y parabrisas), gana el chasis y el conflicto se reporta.
_ENV = CHASIS["envolvente"]
_env_x = np.array([e["x"] for e in _ENV])
_env_hi = np.array([e["y_hi"] for e in _ENV]) + MARGEN_ARRIBA
_env_z = np.array([e["z"] for e in _ENV]) + MARGEN_LADO


def techo_min_chasis(x):
    if x < _env_x[0] or x > _env_x[-1]:
        return 0.0
    return float(np.interp(x, _env_x, _env_hi))


def techo(x):
    """Altura del centro (cofre / techo / cubierta). Lámina, levantada por el chasis con
    una transición suave para no dejar un escalón donde arranca el conflicto."""
    y = techo_ref(x)
    ymin = max(techo_min_chasis(x - 0.06), techo_min_chasis(x), techo_min_chasis(x + 0.06))
    return max(y, ymin)


def semi(x):
    return semi_ref(x)


# ---- líneas de carácter (diseño sobre lo medido). Alturas en m, z como fracción del
#      semiancho local para que sigan la planta automáticamente. -----------------------
Y_HOMBRO = tabla([(-0.134, 0.395), (-0.08, 0.36), (0.0, 0.33), (0.15, 0.42), (0.35, 0.51),
                  (0.55, 0.555), (0.85, 0.575), (1.3, 0.575), (1.9, 0.575), (2.3, 0.585),
                  (2.68, 0.605), (2.95, 0.60), (3.10, 0.585), (3.20, 0.578), (3.246, 0.575)])
Y_FALDON = tabla([(-0.134, 0.372), (-0.10, 0.20), (0.0, 0.21), (0.3, 0.26), (0.55, 0.29),
                  (1.0, 0.30), (2.0, 0.30), (2.68, 0.30), (3.0, 0.32), (3.10, 0.40),
                  (3.20, 0.50), (3.246, 0.565)])
# arista de salpicadera / cintura: el borde superior del volumen bajo
# en el cowl (0.85-1.05) la arista y la base del cristal van 25-35 mm más altas que
# lo que pide la lámina: las esquinas dash_hi (0.95, 0.72, ±0.48) quedaban a 8 mm de
# la piel, dentro del sándwich (verificar_piel_v3.py, 2026-09-05)
Y_ARISTA = tabla([(-0.134, 0.400), (-0.10, 0.43), (0.0, 0.48), (0.15, 0.55), (0.35, 0.65),
                  (0.55, 0.715), (0.70, 0.73), (0.85, 0.745), (1.05, 0.74), (1.4, 0.71),
                  (1.9, 0.71), (2.3, 0.73), (2.55, 0.765), (2.68, 0.78), (2.85, 0.75),
                  (3.0, 0.70), (3.10, 0.66), (3.20, 0.61), (3.246, 0.58)])
K_ARISTA = tabla([(-0.134, 0.85), (-0.05, 0.90), (0.2, 0.93), (0.55, 0.92), (1.0, 0.95),
                  (1.6, 0.96), (2.2, 0.95), (2.68, 0.93), (3.0, 0.92), (3.246, 0.85)])
# base del cristal (DLO): altura; el ancho lo da la planta medida (canopy / luneta)
Y_DLO = tabla([(0.75, 0.755), (0.95, 0.785), (1.2, 0.80), (1.6, 0.80), (2.0, 0.80),
               (2.3, 0.80), (2.55, 0.79), (2.9, 0.75)])
# hondonada del cofre entre salpicaderas (m por debajo del lomo central)
VALLE = tabla([(-0.134, 0.0), (0.0, 0.015), (0.25, 0.04), (0.55, 0.05), (0.8, 0.035),
               (0.95, 0.0), (2.3, 0.0), (2.6, 0.035), (2.9, 0.05), (3.1, 0.025),
               (3.246, 0.0)])
X_CANOPY0, X_CANOPY1 = 0.75, 2.52     # de la planta medida
X_LUNETA0, X_LUNETA1 = 2.31, 2.91


def z_cristal(x):
    """Semiancho de la base del cristal en x: canopy adelante, luneta atrás. En el
    tramo donde conviven (2.35-2.62) se funde uno en otro con una S suave: si se
    salta del ancho del cristal lateral al de la luneta de una estación a la otra,
    la superficie se pellizca detrás de la puerta."""
    c, l = canopy_ref(x), luneta_ref(x)
    if x <= 2.35:
        return c
    if x >= 2.62:
        return l
    t = (x - 2.35) / 0.27
    t = t * t * (3 - 2 * t)
    return c * (1 - t) + l * t


# ============================================================================
# 3. SECCIÓN — media sección de 12 puntos (y, z) en la estación x
# ============================================================================
N_MEDIA = 12


def seccion(x):
    # Catmull-Clark encoge lo convexo ~1 %: se compensa para que la piel subdividida
    # caiga en la cota, no la jaula
    zs = max(semi(x), 0.26) + 0.006
    yt = techo(x) + 0.012
    # piso de la piel: plano entre ruedas; en la cola sigue el rebaje medido (el
    # difusor sube hasta la arista), y en la punta el labio queda a la altura del faldón
    yb = Y_PISO if piso_ref(x) < 0.15 else min(piso_ref(x), yt - 0.02)
    if x < -0.05:                                   # labio de la nariz
        yb = max(yb, Y_FALDON(x) - 0.06) if x > -0.12 else Y_FALDON(x) - 0.01
    yh = min(max(Y_HOMBRO(x), yb + 0.02), yt - 0.01)
    yf = min(max(Y_FALDON(x), yb + 0.01), yh - 0.01)
    ya = min(max(Y_ARISTA(x), yh + 0.01), yt + 0.03)
    za = zs * K_ARISTA(x)
    zc = z_cristal(x)
    en_cristal = zc > 0.05
    if en_cristal:
        y8 = Y_DLO(x)
        z8 = min(zc, za - 0.04)
        y8 = min(max(y8, ya + 0.005), yt - 0.01)
        # repisa entre la arista y el cristal: ligeramente convexa
        y7 = ya + 0.62 * (y8 - ya) + 0.012
        z7 = za + 0.5 * (z8 - za)
        # invernadero: burbuja con tumblehome
        z10 = 0.62 * z8
        y10 = yt - 0.030
        z9 = z8 - 0.42 * (z8 - z10)
        y9 = y8 + 0.56 * (y10 - y8) + 0.025
    else:
        v = VALLE(x)
        base = min(ya, yt)
        z7, y7 = 0.74 * za, base - v
        z8, y8 = 0.52 * za, yt - 0.70 * v
        z9, y9 = 0.31 * za, yt - 0.30 * v
        z10, y10 = 0.14 * za, yt - 0.06 * v
    # flanco: casi vertical con un ligero recogido bajo el hombro
    z4, y4 = zs - 0.012, yf + 0.55 * (yh - yf)
    z3 = zs - 0.030
    z2 = zs - 0.075
    y2 = yb + 0.012
    z1 = zs - 0.14
    pts = [(yb, 0.0), (yb, z1), (y2, z2), (yf, z3), (y4, z4), (yh, zs),
           (ya, za), (y7, z7), (y8, z8), (y9, z9), (y10, z10), (yt, 0.0)]
    return pts


# ============================================================================
# 4. ESTACIONES y CREASES
# ============================================================================
ESTACIONES = [-0.134, -0.105, -0.06, 0.0, 0.08, 0.18, 0.30, 0.42, 0.55, 0.68, 0.80,
              0.92, 1.04, 1.18, 1.32, 1.46, 1.62, 1.78, 1.94, 2.08, 2.22, 2.36, 2.50,
              2.64, 2.78, 2.92, 3.04, 3.13, 3.20, 3.246]


def crease_anillo(i, x):
    """Firmeza de la arista longitudinal del anillo i en la estación x."""
    if i == 1:
        return 0.35                                  # canto del piso
    if i == 2:
        return 0.80                                  # quilla del estribo
    if i == 3:
        return 0.55                                  # tope del faldón
    if i == 5:                                       # hombro: firme en las salpicaderas
        return 0.70 if (x < 0.95 or x > 2.35) else 0.30
    if i == 6:                                       # arista de salpicadera
        return 0.95 if (x < 0.95 or x > 2.35) else 0.65
    if i == 8:                                       # base del cristal
        return 0.95 if z_cristal(x) > 0.05 else 0.0
    if i == 10:
        return 0.30 if z_cristal(x) > 0.05 else 0.0
    return 0.0


def construir():
    """Vértices, caras (cuadriláteros + 2 tapas), creases y atributos por cara."""
    verts, anillos = [], []
    n_ring = 2 * N_MEDIA - 2
    for x in ESTACIONES:
        media = seccion(x)
        ring = []
        for k, (y, z) in enumerate(media):              # lado +z
            ring.append(len(verts))
            verts.append((x, y, z))
        for k in range(N_MEDIA - 2, 0, -1):             # espejo, sin repetir polos
            y, z = media[k]
            ring.append(len(verts))
            verts.append((x, y, -z))
        anillos.append(ring)

    faces, attr = [], []                                 # attr: (anillo, estacion, x)
    for i in range(len(anillos) - 1):
        A, B = anillos[i], anillos[i + 1]
        xm = 0.5 * (ESTACIONES[i] + ESTACIONES[i + 1])
        for k in range(n_ring):
            k2 = (k + 1) % n_ring
            faces.append((A[k], B[k], B[k2], A[k2]))
            # índice de anillo de la cara = el menor de sus dos anillos (0..10),
            # espejado para el lado -z
            kk = k if k < N_MEDIA else n_ring - k - 1
            attr.append((kk, i, xm))
    # Tapas en ESCALERA (cuadriláteros que cruzan el plano de simetría), no n-gon: un
    # n-gon de 22 lados con crease se pliega al subdividir y el booleano exacto de
    # Blender lee entonces el sólido al revés (verificado 2026-09-04).
    for ring, invertir, tag, est in ((anillos[0], True, -1, 0),
                                     (anillos[-1], False, -2, len(anillos) - 2)):
        for k in range(N_MEDIA - 1):
            a, b = ring[k], ring[k + 1]
            ma, mb = ring[(n_ring - k) % n_ring], ring[(n_ring - k - 1) % n_ring]
            f = []
            for v in (a, b, mb, ma):
                if v not in f:
                    f.append(v)
            faces.append(tuple(reversed(f)) if invertir else tuple(f))
            attr.append((tag, est, ESTACIONES[est if tag == -1 else -1]))

    # OJO con el espejo: el VÉRTICE en la posición k (k >= N_MEDIA) es el anillo
    # n_ring - k; la CARA entre k y k+1 lleva el anillo menor, n_ring - k - 1. Usar
    # la fórmula de cara para las aristas desfasaba un anillo los creases del lado
    # -z y dejaba la carrocería 5-9 mm asimétrica (visto en el STL, 2026-09-05).
    creases = []
    for i in range(len(anillos) - 1):
        A, B = anillos[i], anillos[i + 1]
        xm = 0.5 * (ESTACIONES[i] + ESTACIONES[i + 1])
        for k in range(n_ring):
            kk = k if k < N_MEDIA else n_ring - k
            w = crease_anillo(kk, xm)
            if w > 0:
                creases.append((A[k], B[k], w))
    # tapas: la nariz con arista de flecha arriba, la cola con canto duro alrededor
    for ring, w_top, w_bot in ((anillos[0], 0.75, 0.30), (anillos[-1], 0.95, 0.60)):
        for k in range(n_ring):
            a, b = ring[k], ring[(k + 1) % n_ring]
            kk = k if k < N_MEDIA else n_ring - k - 1
            creases.append((a, b, w_top if kk >= 6 else w_bot))

    return {"verts": [[round(float(c), 5) for c in v] for v in verts],
            "faces": faces, "creases": [(a, b, round(w, 3)) for a, b, w in creases],
            "attr": [(int(a), int(e), round(float(x), 4)) for a, e, x in attr],
            "n_media": N_MEDIA, "estaciones": ESTACIONES,
            "paquete": {"x_morro": X_MORRO, "x_cola": X_COLA, "semi": SEMI, "alto": ALTO,
                        "eje_del": EJE_DEL, "eje_tras": EJE_TRAS, "y_piso": Y_PISO,
                        "x_canopy": [X_CANOPY0, X_CANOPY1],
                        "x_luneta": [X_LUNETA0, X_LUNETA1]},
            "ruedas": [{"x": EJE_DEL, "z": Z_RUEDA_DEL, "R": R_DEL, "W": ANCHO_LL, "rin": 13},
                       {"x": EJE_DEL, "z": -Z_RUEDA_DEL, "R": R_DEL, "W": ANCHO_LL, "rin": 13},
                       {"x": EJE_TRAS, "z": Z_RUEDA_TRAS, "R": R_TRAS, "W": ANCHO_LL, "rin": 14},
                       {"x": EJE_TRAS, "z": -Z_RUEDA_TRAS, "R": R_TRAS, "W": ANCHO_LL, "rin": 14}],
            "cristal": {"canopy": [[round(float(x), 3), round(float(c), 4)]
                                   for x, c in zip(CURVAS["cenital"]["x"],
                                                   CURVAS["cenital"]["cristal"])],
                        "luneta": [[round(float(x), 3), round(float(c), 4)]
                                   for x, c in zip(CURVAS["cenital"]["x"],
                                                   CURVAS["cenital"]["luneta"])],
                        "y_dlo": [[x, round(Y_DLO(x), 4)] for x in
                                  np.arange(0.75, 2.95, 0.05).round(3).tolist()]}}


# ============================================================================
# 5. VERIFICACIÓN — piel contra chasis y contra la lámina, en mm
# ============================================================================
def verificar(j):
    V = np.array(j["verts"])
    print("\n    VERIFICACION piel vs chasis (margen minimo: tubo + "
          f"{MARGEN_ARRIBA*1000:.0f} mm arriba, {MARGEN_LADO*1000:.0f} mm de lado)")
    peor = 0.0
    for e in _ENV:
        x = e["x"]
        yt = techo(x)
        falta = (e["y_hi"] + MARGEN_ARRIBA) - yt
        if falta > peor:
            peor = falta
        s = seccion(x)
        # semiancho de la piel a la altura del tubo más ancho: se toma el hombro
        zh = s[5][1]
        if zh < e["z"] + MARGEN_LADO:
            print(f"    ! x={x:.2f}: flanco {zh:.3f} < tubo {e['z']:.3f}+margen")
    print(f"    techo: {'OK, la piel cubre todo el chasis' if peor <= 1e-6 else f'FALTA {peor*1000:.0f} mm'}")
    print("    conflicto lamina vs chasis (parabrisas): donde el techo medido queda bajo el tubo")
    for x in (0.92, 1.04, 1.18, 1.32, 1.46):
        print(f"      x={x:.2f}  lamina {techo_ref(x):.3f}  minimo chasis {techo_min_chasis(x):.3f}"
              f"  modelo {techo(x):.3f}  (+{(techo(x)-techo_ref(x))*1000:.0f} mm)")
    print(f"    largo {V[:,0].max()-V[:,0].min():.3f}  ancho {2*V[:,2].max():.3f}  "
          f"alto {V[:,1].max():.3f}  piso {V[:,1].min():.3f}")


def lamina(j):
    """Tres vistas de la jaula (anillos) sobre las curvas de la referencia."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    V = np.array(j["verts"])
    n_ring = 2 * N_MEDIA - 2
    rings = [V[i * n_ring:(i + 1) * n_ring] for i in range(len(ESTACIONES))]
    fig, ax = plt.subplots(2, 2, figsize=(18, 10), facecolor="#0d1117")
    for a in ax.flat:
        a.set_facecolor("#0d1117")
        a.set_aspect("equal")
        a.tick_params(colors="#7d8590", labelsize=8)
        for s in a.spines.values():
            s.set_color("#30363d")
    lat = CURVAS["lateral"]
    cen = CURVAS["cenital"]
    a = ax[0, 0]
    a.plot(lat["x"], lat["techo"], color="#f0a868", lw=1.0, label="lámina")
    for r in rings:
        a.plot(r[:, 0], r[:, 1], color="#c9d1d9", lw=0.6)
    for i in range(N_MEDIA):
        a.plot([r[i, 0] for r in rings], [r[i, 1] for r in rings], color="#5b8ddb", lw=0.7)
    for w in j["ruedas"][::2]:
        a.add_patch(plt.Circle((w["x"], w["R"]), w["R"], fill=False, color="#7d8590"))
    a.set_title("LATERAL — anillos de la jaula sobre la silueta medida", color="#c9d1d9", loc="left")
    a = ax[0, 1]
    a.plot(cen["x"], cen["semiancho"], color="#f0a868", lw=1.0)
    a.plot(cen["x"], cen["cristal"], color="#5b8ddb", lw=1.0)
    a.plot(cen["x"], cen["luneta"], color="#9b6bd6", lw=1.0)
    for r in rings:
        a.plot(r[:, 0], r[:, 2], color="#c9d1d9", lw=0.6)
    for i in range(N_MEDIA):
        a.plot([r[i, 0] for r in rings], [r[i, 2] for r in rings], color="#5b8ddb", lw=0.7)
    a.set_title("CENITAL", color="#c9d1d9", loc="left")
    for a, xs, t in ((ax[1, 0], [-0.105, 0.0, 0.18, 0.42, 0.55, 0.80], "SECCIONES ADELANTE"),
                     (ax[1, 1], [1.18, 1.62, 2.08, 2.50, 2.78, 3.04, 3.20], "SECCIONES ATRÁS")):
        for x in xs:
            s = seccion(x)
            a.plot([p[1] for p in s] + [-p[1] for p in s[::-1]],
                   [p[0] for p in s] + [p[0] for p in s[::-1]], lw=1.0, label=f"x={x:.2f}")
        a.plot(CURVAS["frontal"]["z"], CURVAS["frontal"]["techo"], color="#f0a868", lw=0.8, ls="--")
        a.plot(CURVAS["trasera"]["z"], CURVAS["trasera"]["techo"], color="#f85149", lw=0.8, ls="--")
        a.axhline(0, color="#30363d")
        a.set_xlim(-1.0, 1.0)
        a.set_ylim(-0.05, 1.15)
        a.legend(fontsize=7, facecolor="#161b22", labelcolor="#c9d1d9", ncol=2)
        a.set_title(t + "  (naranja: envolvente frontal · rojo: trasera)", color="#c9d1d9", loc="left")
    fig.tight_layout()
    out = os.path.join(HERE, "carro3d-jaula.png")
    fig.savefig(out, dpi=105, facecolor="#0d1117")
    return out


def main():
    j = construir()
    out = os.path.join(RAIZ, "cad", "carro-v3-jaula.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(j, f, separators=(",", ":"))
    print(f"OK  {out}: {len(j['verts'])} vertices, {len(j['faces'])} caras, "
          f"{len(j['creases'])} aristas con crease")
    verificar(j)
    try:
        print(f"OK  {lamina(j)}")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
