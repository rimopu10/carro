# -*- coding: utf-8 -*-
"""
Superficie de la carrocería v2 — estudio de proporciones.

Reconstruye la carrocería a partir de la imagen de referencia del dueño (lámina de
concepto tipo Aston Martin con puertas de gaviota). La lámina NO es un plano: sus seis
vistas no son ortográficamente consistentes entre sí, así que aquí se toma de ella el
LENGUAJE (silueta fastback, caderas sobre las 4 ruedas, gaviota profunda, morro largo
y bajo, cola trunca con barra de luz) y se reconstruye la superficie sobre los puntos
duros reales del chasis.

Método: la carrocería son estaciones transversales a lo largo de x. Cada estación se
define por tres puntos de control — quilla (piso), hombro (el punto más ancho) y techo —
unidos por dos cuartos de superelipse. Eso da un lomo lleno tipo "cadera de 33 Stradale"
sin tener que modelar splines a mano. Los pasos de rueda se recortan empujando los
puntos de la piel que caen dentro del arco hasta el propio arco.

Escenario D (aprobado condicionalmente 2026-08-16): 3.35 × 1.78 × 1.03 m, sin tocar
batalla ni trocha. El ancho no es capricho: con 1.62 m las llantas sobresalían 38.5 mm.

CORRECCIÓN DE VOLADIZOS (2026-08-18). Medida la lámina contra el modelo, los voladizos
estaban INVERTIDOS: la referencia es un carro de morro largo (684 mm) y cola corta
(566), y esto tenía 550 y 670. Eso —no la superficie blanda— era la razón principal de
que no se pareciera: el ojo lee dónde caen las ruedas dentro del cuerpo antes que
cualquier línea de carácter. Corregido a 3.38 × 1.78 × 1.03 SIN tocar batalla, ejes,
suspensión ni lista de corte. La línea de techo también se pegó a la lámina, pero solo
fuera de los ejes; entre ejes mandan los puntos duros del chasis y el conflicto que
queda (+101 mm en el parabrisas) se reporta, no se esconde. Ver verificar().

Salidas:
  calculos/carroceria-proporciones.png   lámina de vistas para juzgar la proporción
  calculos/carroceria-superficie.json    la superficie, para el visor 3D y el CNC
  (y calculos/blueprint.py genera de aquí las vistas ortográficas del paquete)

Correr:  python calculos/carroceria.py
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

# ============================================================================
# 1. PUNTOS DUROS — vienen del chasis, no se negocian
# ============================================================================
EJE_DEL, R_DEL = 0.550, 0.2876          # 175/70R13
EJE_TRAS, R_TRAS = 2.680, 0.3005        # 175/70R14 sobre el QS273
Z_RUEDA_DEL, Z_RUEDA_TRAS = 0.750, 0.760
ANCHO_LL = 0.177
LIBRE = 0.160                            # altura libre al piso

# geometría de cabina ya validada por FEM con la gaviota (2026-08-16)
X_COWL, Y_COWL = 0.950, 0.720           # pie del pilar A (nodo dash_hi)
X_HDR,  Y_HDR = 1.450, 0.950            # cabecera del parabrisas (nodo hdr)
X_ARCO, Y_ARCO = 2.020, 1.010           # corona del arco principal (nodo mh_hi)
Z_ESPINAZO = 0.150                      # riel de techo = eje de bisagra de la gaviota

# ---- VOLADIZOS: se toman medidos de la lámina, no a ojo -----------------------------
# Hallazgo del 2026-08-18: los voladizos estaban INVERTIDOS respecto a la referencia.
# La lámina es un carro de morro largo y cola corta; esto tenía morro corto (550 mm,
# faltaban 134) y cola larga (670 mm, sobraban 104). Eso es lo que hacía que no se
# pareciera — el ojo lee dónde caen las ruedas dentro del cuerpo antes que cualquier
# línea de carácter, y ninguna cantidad de superficie lo compensa.
#
# La corrección NO toca mecánica: la batalla se queda en 2.130, los ejes no se mueven,
# la suspensión y la lista de corte no se enteran. Solo cambia dónde termina la lámina
# de carrocería adelante y atrás. Verificado contra el chasis (x de 0.100 a 3.000):
# la cola nueva lo sigue cubriendo con 246 mm (hoy vuela 350, o sea vuela MENOS), y el
# morro pasa a volar 234 mm en vez de 100 — carrocería en voladizo, no estructura, y
# de paso abre el espacio de nariz que hacía falta para los controladores.
_SIL = json.load(open(os.path.join(HERE, "..", "ref", "silueta-referencia.json"),
                      encoding="utf-8"))
BATALLA = EJE_TRAS - EJE_DEL             # 2.130 — punto duro, no se negocia
VOL_DEL = _SIL["voladizo_del"] * BATALLA     # 0.684 — lo que pide la lámina
VOL_TRAS = _SIL["voladizo_tras"] * BATALLA   # 0.566
X_MORRO = EJE_DEL - VOL_DEL              # -0.134 (el origen x del chasis es arbitrario)
X_COLA = EJE_TRAS + VOL_TRAS             # 3.246

# Esquema viejo del que se remapea. Se deja explícito para que el cambio sea auditable
# y reversible, en vez de quedar horneado en las coordenadas de EST.
_MORRO_0, _VOL_DEL_0, _VOL_TRAS_0 = 0.000, 0.550, 0.670


def remap_x(x):
    """Lleva una x del esquema viejo al corregido, dejando la batalla intacta.

    Tres tramos: el morro se estira, el entre-ejes NO se toca (ahí viven el cowl, la
    cabecera y el arco, que están validados por FEM y son puntos duros), y la cola se
    encoge. Todo lo que dependa de coordenadas x del esquema viejo —estaciones, faldón,
    umbrales de luz— tiene que pasar por aquí, o se desalinea con la piel.
    """
    if x <= EJE_DEL:
        return X_MORRO + (x - _MORRO_0) * (VOL_DEL / _VOL_DEL_0)
    if x >= EJE_TRAS:
        return EJE_TRAS + (x - EJE_TRAS) * (VOL_TRAS / _VOL_TRAS_0)
    return x


LARGO, ANCHO, ALTO = X_COLA - X_MORRO, 1.780, 1.030      # 3.380 × 1.780 × 1.030
SEMI = ANCHO / 2                        # 0.890 — deja 41.5 mm de salpicadera sobre la llanta

# ============================================================================
# 2. ESTACIONES — (x, quilla, hombro, techo)
#    quilla = (semiancho, y) del piso · hombro = (semiancho, y) del punto más ancho
#    techo  = (semiancho, y) de la cubierta · n_lo/n_hi = llenura de cada lóbulo
# ============================================================================
#        x     z_q   y_q    z_h   y_h    z_t   y_t   n_lo n_hi
EST = [
    (0.000, 0.170, 0.300, 0.240, 0.345, 0.110, 0.390, 2.6, 2.4),  # punta
    (0.120, 0.380, 0.235, 0.520, 0.330, 0.310, 0.430, 2.8, 2.6),
    (0.300, 0.530, 0.185, 0.720, 0.350, 0.470, 0.510, 3.0, 2.8),
    (0.550, 0.600, 0.170, 0.890, 0.400, 0.560, 0.610, 3.2, 3.0),  # eje delantero — cadera
    (0.750, 0.605, 0.165, 0.860, 0.420, 0.580, 0.660, 3.2, 3.0),
    (0.950, 0.610, 0.165, 0.845, 0.440, 0.560, 0.720, 3.2, 2.8),  # cowl: nace el parabrisas
    (1.200, 0.615, 0.170, 0.855, 0.455, 0.500, 0.845, 3.2, 2.4),  # parabrisas a media altura
    (1.450, 0.620, 0.180, 0.865, 0.465, 0.430, 0.950, 3.2, 2.3),  # cabecera
    (1.700, 0.625, 0.190, 0.875, 0.475, 0.420, 1.020, 3.2, 2.4),
    (1.900, 0.630, 0.200, 0.885, 0.485, 0.415, 1.030, 3.2, 2.5),  # techo máximo
    (2.020, 0.630, 0.210, 0.890, 0.495, 0.405, 1.025, 3.2, 2.5),  # arco principal
    (2.300, 0.625, 0.225, 0.890, 0.515, 0.375, 0.965, 3.2, 2.7),  # arranca el fastback
    (2.680, 0.605, 0.245, 0.885, 0.535, 0.330, 0.840, 3.2, 2.9),  # eje trasero — cadera
    (3.000, 0.560, 0.270, 0.830, 0.530, 0.290, 0.710, 3.0, 3.0),
    (3.200, 0.480, 0.290, 0.740, 0.510, 0.250, 0.610, 2.8, 3.0),
    (3.350, 0.360, 0.310, 0.560, 0.470, 0.180, 0.520, 2.6, 2.8),  # cola trunca (Kamm)
]
# Las x de arriba están en el esquema viejo, que es como se dibujaron y como se pueden
# comparar con las versiones anteriores. La corrección de voladizos se aplica aquí, en
# un solo lugar; las secciones (semianchos y alturas) no se tocan.
EST = [(remap_x(e[0]),) + tuple(e[1:]) for e in EST]

MARGEN_REF = 0.030      # se descarta al comparar: basura de borde del recorte


def _ajustar_techo_a_lamina():
    """Pega la línea de techo a la lámina SOLO donde no hay punto duro.

    Entre ejes no se toca nada: ahí viven el cowl (dash_hi), la cabecera (hdr) y la
    corona del arco (mh_hi), que están validados por FEM y son los que sostienen a la
    gaviota. Si la lámina pide otra cosa ahí, gana la ingeniería — pero el conflicto se
    reporta en mm en verificar(), no se esconde.

    Fuera de los ejes —morro y cola— no hay estructura que respetar: el chasis termina
    en x=3.000 y empieza en x=0.100. Ahí la lámina manda, y se le hace caso. El ajuste
    se desvanece hacia cada eje para no meter un pico en la unión.
    """
    xr = np.array(_SIL["x"]) * BATALLA + EJE_DEL
    yr = np.array(_SIL["techo"]) * BATALLA
    ok = (xr >= X_MORRO + MARGEN_REF) & (xr <= X_COLA - MARGEN_REF)
    xr, yr = xr[ok], yr[ok]

    fuera = []
    for e in EST:
        x = e[0]
        if EJE_DEL <= x <= EJE_TRAS:
            fuera.append(e)
            continue
        # np.interp fija el valor del extremo fuera de rango, y eso es lo correcto
        # aquí: la punta y la cola caen en el margen descartado, y lo que queremos es
        # que hereden la última altura BUENA medida. Saltárselas dejaba la cola Kamm
        # en su valor viejo y la hacía desplomarse 137 mm en los últimos 35.
        objetivo = float(np.interp(x, xr, yr))
        # peso 0 en el eje -> 1 en la punta: la corrección entra suave
        d = (EJE_DEL - x) / VOL_DEL if x < EJE_DEL else (x - EJE_TRAS) / VOL_TRAS
        w = min(1.0, max(0.0, d))
        fuera.append(e[:6] + (e[6] + (objetivo - e[6]) * w,) + e[7:])
    return fuera


EST = _ajustar_techo_a_lamina()

N_LOBULO = 34      # puntos por cuarto de superelipse (alto: los materiales se cortan
N_PLANO = 7        # sobre la malla, y con pocos puntos el borde del cristal escalona)


def seccion(est, n_lo=N_LOBULO, n_hi=N_LOBULO):
    """Media sección (z>=0), de la quilla al techo, en orden."""
    x, zq, yq, zh, yh, zt, yt, e_lo, e_hi = est
    pts = [(0.0, yq)]
    # cos(π/2·k/n) sale ligeramente NEGATIVO por redondeo cuando k=n, y elevarlo a
    # potencia fraccionaria da nan — vértices inválidos que el visor dibuja como
    # agujeros. Se recorta a [0,1].
    co = lambda u: max(0.0, min(1.0, float(np.cos(u))))
    si = lambda u: max(0.0, min(1.0, float(np.sin(u))))
    for k in range(1, N_PLANO):                       # piso plano (undertray)
        pts.append((zq * k / (N_PLANO - 1), yq))
    for k in range(1, n_lo + 1):                      # lóbulo bajo: quilla -> hombro
        u = np.pi / 2 * k / n_lo
        pts.append((zh + (zq - zh) * co(u) ** (2 / e_lo),
                    yq + (yh - yq) * si(u) ** (2 / e_lo)))
    for k in range(1, n_hi + 1):                      # lóbulo alto: hombro -> techo
        u = np.pi / 2 * k / n_hi
        pts.append((zt + (zh - zt) * co(u) ** (2 / e_hi),
                    yh + (yt - yh) * si(u) ** (2 / e_hi)))
    for k in range(1, N_PLANO):                       # techo hacia el eje
        pts.append((zt * (1 - k / (N_PLANO - 1)), yt))
    return [(x, y, z) for z, y in pts]


def recortar_pasos(p):
    """Empuja fuera del arco de rueda los puntos de piel que caen dentro de él."""
    x, y, z = p
    az = abs(z)
    if az < 0.45:
        return p
    peso = min(1.0, (az - 0.45) / 0.14)                # se desvanece hacia el centro
    for xa, ra in ((EJE_DEL, R_DEL + 0.048), (EJE_TRAS, R_TRAS + 0.048)):
        d = np.hypot(x - xa, y - LIBRE)
        if d < ra and y < LIBRE + ra:
            k = ra / max(d, 1e-6)
            xn = xa + (x - xa) * k
            yn = LIBRE + (y - LIBRE) * k
            x, y = x + (xn - x) * peso, y + (yn - y) * peso
    return (x, y, z)


def interp_est(x):
    """Estación interpolada en cualquier x (las de EST son puntos de control)."""
    xs = [e[0] for e in EST]
    i = int(np.clip(np.searchsorted(xs, x) - 1, 0, len(EST) - 2))
    t = (x - xs[i]) / (xs[i + 1] - xs[i])
    a, b = EST[i], EST[i + 1]
    return tuple(a[k] + (b[k] - a[k]) * t for k in range(9))


def malla(nx=92):
    """Rejilla de la piel: nx anillos, cada uno con el mismo número de puntos, así que
    las celdas (i,k) forman un dominio paramétrico donde recortar la puerta."""
    xs = np.linspace(EST[0][0], EST[-1][0], nx)
    anillos, n_media = [], None
    for x in xs:
        media = [recortar_pasos(p) for p in seccion(interp_est(x))]
        espejo = [(px, py, -pz) for (px, py, pz) in reversed(media[1:-1])]
        anillos.append(media + espejo)
        n_media = len(media)
    return xs, anillos, n_media


# ============================================================================
# 3. RECORTE DE LA PUERTA DE GAVIOTA — en el dominio paramétrico de la malla
# ============================================================================
X_PUERTA_F, X_PUERTA_T = 1.055, 2.115     # bordes delantero y trasero del hueco
Y_ESTRIBO = 0.430                          # línea de umbral


def techo_puerta(x):
    """Altura máxima que alcanza la puerta en la estación x.

    El borde delantero del hueco NO es vertical: sigue el pilar A, del estribo en
    x=X_PUERTA_F hasta la cabecera en x=X_HDR. Si se recorta con una x constante, el
    hueco se come el parabrisas y al abrir la puerta se lleva el cristal frontal.
    El borde trasero hace lo mismo contra la pierna del arco principal.
    """
    if x < X_PUERTA_F or x > X_PUERTA_T:
        return None
    if x < X_HDR:                                   # pilar A
        t = (x - X_PUERTA_F) / (X_HDR - X_PUERTA_F)
        return Y_ESTRIBO + (y_techo(X_HDR) - Y_ESTRIBO) * t ** 1.55
    if x <= X_ARCO:                                 # tramo de techo completo
        return y_techo(x) + 0.01
    t = (x - X_ARCO) / (X_PUERTA_T - X_ARCO)        # pierna del arco
    return y_techo(X_ARCO) - (y_techo(X_ARCO) - Y_ESTRIBO) * t ** 0.70


def rango_puerta(x, media):
    """Índices (k0,k1) de la MEDIA sección (z>=0) que pertenecen a la puerta, o None.

    La media sección va: eje-piso -> quilla -> hombro -> techo -> eje-techo. La puerta
    arranca donde la piel cruza el estribo subiendo, y termina en lo que llegue antes:
    el espinazo (|z| <= Z_ESPINAZO) o el borde inclinado de `techo_puerta`.
    """
    ylim = techo_puerta(x)
    if ylim is None or ylim <= Y_ESTRIBO + 0.02:
        return None
    subida = [j for j, p in enumerate(media) if p[1] >= Y_ESTRIBO]
    if not subida:
        return None
    k0 = min(subida)
    # el espinazo solo existe en el tramo alto del anillo: se filtra por altura
    espinazo = [j for j, p in enumerate(media) if p[2] <= Z_ESPINAZO and p[1] > 0.75]
    tope = [j for j in range(k0, len(media)) if media[j][1] > ylim]
    cand = [c for c in (min(espinazo) if espinazo else None,
                        min(tope) if tope else None) if c is not None]
    if not cand:
        return None
    k1 = min(cand)
    return (k0, k1) if k1 > k0 + 1 else None


def celdas(xs, anillos, n_media):
    """Marca qué celdas (i,k) son puerta izquierda ('pi'), derecha ('pd') o cuerpo.

    El semianillo espejo se guardó en orden inverso, así que el índice espejo de la
    media j es 2*n_media-2-j. Derivar la puerta derecha de ese mapeo (en vez de
    volver a buscarla) garantiza que las dos salgan simétricas.
    """
    marca = {}
    total = 2 * n_media - 2
    for i, (x, an) in enumerate(zip(xs, anillos)):
        r = rango_puerta(x, an[:n_media])
        if not r:
            continue
        k0, k1 = r
        for k in range(k0, k1):
            marca[(i, k)] = "pi"
        for k in range(total - k1, total - k0):
            marca[(i, k % total)] = "pd"
    return marca


# ---- materiales: lo que hace que una carrocería lofteada deje de verse jabón --------
Y_CINTURA = [(X_COWL, 0.700), (1.200, 0.686), (X_HDR, 0.682), (1.900, 0.706),
             (X_ARCO, 0.742), (2.130, 0.800)]
# El faldón no es una línea de flotación: sube en los extremos, que es lo que lo hace
# leer como capa técnica y no como el carro a medio hundir.
FALDON = [(remap_x(x), y) for x, y in
          [(0.00, 0.330), (0.30, 0.292), (0.55, 0.288), (1.20, 0.276), (1.90, 0.282),
           (2.68, 0.300), (3.10, 0.340), (3.35, 0.392)]]

# Umbrales de las firmas de luz, también en el esquema viejo y remapeados: si no pasan
# por remap_x se despegan de la piel al mover los voladizos.
X_LUZ_T = remap_x(3.235)                 # arranque de la barra trasera
X_LUZ_D = remap_x(0.215)                 # fin de las cejas delanteras


def material(x, p):
    """Material de un punto de la piel: pintura, vidrio, negro o luz."""
    y, z = p[1], abs(p[2])
    if X_COWL <= x <= 2.130:
        cintura = np.interp(x, [c[0] for c in Y_CINTURA], [c[1] for c in Y_CINTURA])
        if y > cintura and (x < X_HDR or z > Z_ESPINAZO + 0.030):
            return "vidrio"
    if x > X_LUZ_T and 0.404 <= y <= 0.474:
        return "luz_t"                     # barra trasera continua
    if x < X_LUZ_D and 0.330 <= y <= 0.386 and z > 0.15:
        return "luz_d"                     # cejas delanteras
    # el interior del paso de rueda va oscuro: sin eso el arco no se lee y el carro
    # parece flotar sobre las llantas
    if z > 0.545:
        for xa, ra in ((EJE_DEL, R_DEL + 0.048), (EJE_TRAS, R_TRAS + 0.048)):
            if abs(np.hypot(x - xa, y - LIBRE) - ra) < 0.042 and y < LIBRE + ra:
                return "negro"
    if y < np.interp(x, [f[0] for f in FALDON], [f[1] for f in FALDON]):
        return "negro"
    return "pintura"


def superficies(xs, anillos, marca):
    """Devuelve {(grupo, material): [triángulos]} — grupo es cuerpo/pi/pd."""
    out = {}
    def add(g, m, t):
        out.setdefault((g, m), []).append(t)
    for i in range(len(anillos) - 1):
        A, B, x = anillos[i], anillos[i + 1], xs[i]
        n = len(A)
        for k in range(n):
            k2 = (k + 1) % n
            g = marca.get((i, k), "cuerpo")
            m = material(x, A[k])
            add(g, m, (A[k], B[k], B[k2]))
            add(g, m, (A[k], B[k2], A[k2]))
    for anillo, x, inv in ((anillos[0], xs[0], False), (anillos[-1], xs[-1], True)):
        c = tuple(np.mean(np.array(anillo), axis=0))
        n = len(anillo)
        for k in range(n):
            k2 = (k + 1) % n
            m = material(x, anillo[k])
            add("cuerpo", m, (c, anillo[k2], anillo[k]) if not inv
                else (c, anillo[k], anillo[k2]))
    return out


def abrir(tris, lado, grados):
    """Gira la puerta sobre el eje de bisagra: la recta del espinazo a |z|=Z_ESPINAZO."""
    yh0 = np.interp(X_HDR, [e[0] for e in EST], [e[6] for e in EST])
    yh1 = np.interp(X_ARCO, [e[0] for e in EST], [e[6] for e in EST])
    P0 = np.array([X_HDR, yh0, lado * Z_ESPINAZO])
    u = np.array([X_ARCO - X_HDR, yh1 - yh0, 0.0])
    u /= np.linalg.norm(u)
    a = np.radians(grados) * (-1 if lado > 0 else 1)   # + gira hacia abajo
    ca, sa = np.cos(a), np.sin(a)
    K = np.array([[0, -u[2], u[1]], [u[2], 0, -u[0]], [-u[1], u[0], 0]])
    R = np.eye(3) + sa * K + (1 - ca) * (K @ K)
    return [tuple(tuple(P0 + R @ (np.array(p) - P0)) for p in t) for t in tris]


# ============================================================================
# 4. CONTEXTO DE ESCALA — ruedas, pilotos y suelo (todo render los lleva)
# ============================================================================
def rueda(xa, R, zc, lado, n=28):
    """Cilindro con el eje en z, apoyado en el piso (centro a y=R)."""
    tris = []
    z0, z1 = lado * (zc - ANCHO_LL / 2), lado * (zc + ANCHO_LL / 2)
    aro = [(xa + R * np.cos(a), R + R * np.sin(a))
           for a in np.linspace(0, 2 * np.pi, n, endpoint=False)]
    for k in range(n):
        A, B = aro[k], aro[(k + 1) % n]
        tris.append(((A[0], A[1], z0), (B[0], B[1], z0), (B[0], B[1], z1)))
        tris.append(((A[0], A[1], z0), (B[0], B[1], z1), (A[0], A[1], z1)))
        for zz, inv in ((z0, False), (z1, True)):
            c = (xa, R, zz)
            tris.append((c, (B[0], B[1], zz), (A[0], A[1], zz)) if inv
                        else (c, (A[0], A[1], zz), (B[0], B[1], zz)))
    return tris


def rin(xa, R, zc, lado, n=24):
    """Cara exterior del rin: disco con 5 rayos. Sin esto la rueda lee como llanta de
    carretilla y arruina la proporción visual."""
    Rr = R * 0.575                                   # rin 13-14" dentro de perfil 70
    zf = lado * (zc + ANCHO_LL / 2 + 0.004)
    tris = []
    aro = [(xa + Rr * np.cos(a), R + Rr * np.sin(a))
           for a in np.linspace(0, 2 * np.pi, n, endpoint=False)]
    for k in range(n):
        A, B = aro[k], aro[(k + 1) % n]
        tris.append(((xa, R, zf), (A[0], A[1], zf), (B[0], B[1], zf)))
    return tris


def _tubo(a, b, r, z, n=10):
    """Tubo de eje a->b (en el plano x-y) y radio r, centrado en el plano z."""
    a, b = np.array([*a, z], float), np.array([*b, z], float)
    eje = b - a
    L = np.linalg.norm(eje)
    if L < 1e-9:
        return []
    u = eje / L
    p = np.array([-u[1], u[0], 0.0])                 # perpendicular en x-y
    q = np.array([0.0, 0.0, 1.0])                    # perpendicular en z
    tris = []
    for k in range(n):
        t0, t1 = 2 * np.pi * k / n, 2 * np.pi * (k + 1) / n
        d0 = r * (np.cos(t0) * p + np.sin(t0) * q)
        d1 = r * (np.cos(t1) * p + np.sin(t1) * q)
        A, B, C, D = a + d0, a + d1, b + d1, b + d0
        tris += [tuple(map(tuple, (A, B, C))), tuple(map(tuple, (A, C, D)))]
        tris += [(tuple(a), tuple(B), tuple(A)), (tuple(b), tuple(D), tuple(C))]
    return tris


def _esfera(c, r, z, n=10):
    c = np.array([*c, z], float)
    tris = []
    for i in range(n):
        for j in range(2 * n):
            v0, v1 = np.pi * i / n, np.pi * (i + 1) / n
            h0, h1 = 2 * np.pi * j / (2 * n), 2 * np.pi * (j + 1) / (2 * n)
            def P(v, h):
                return tuple(c + r * np.array([np.sin(v) * np.cos(h), np.cos(v), np.sin(v) * np.sin(h)]))
            tris += [(P(v0, h0), P(v1, h0), P(v1, h1)), (P(v0, h0), P(v1, h1), P(v0, h1))]
    return tris


def piloto(z):
    """Maniquí sentado con el respaldo reclinado 12°. Cabeza 5 cm bajo el arco."""
    tris = []
    tris += _tubo((1.975, 0.395), (1.845, 0.775), 0.105, z)   # torso reclinado
    tris += _tubo((1.700, 0.330), (1.980, 0.410), 0.072, z)   # muslo
    tris += _tubo((1.410, 0.190), (1.705, 0.335), 0.058, z)   # pierna
    tris += _esfera((1.820, 0.860), 0.100, z)                 # cabeza (tope y=0.960)
    return tris


# ============================================================================
# 5. RENDER — proyección ortográfica y pintor, para controlar el sombreado
# ============================================================================
def base_camara(cam):
    d = np.array(cam, float)
    d /= np.linalg.norm(d)
    up = np.array([0, 1.0, 0])
    if abs(d[1]) > 0.98:
        up = np.array([0, 0, 1.0])
    ex = np.cross(up, d)
    ex /= np.linalg.norm(ex)
    return d, ex, np.cross(d, ex)


LUZ = np.array([0.42, 0.78, 0.46])
LUZ = LUZ / np.linalg.norm(LUZ)


def proyectar(tris, cam, doble_cara=False):
    """Ortográfica + algoritmo del pintor. Con la malla cerrada se descartan las caras
    que dan la espalda a la cámara (por eso el interior ya no se transparenta); las
    puertas son cascarón de una hoja, así que van a doble cara."""
    d, ex, ey = base_camara(cam)
    out = []
    for t in tris:
        P = np.array(t, float)
        n = np.cross(P[1] - P[0], P[2] - P[0])
        ln = np.linalg.norm(n)
        if ln < 1e-12:
            continue
        n /= ln
        frente = np.dot(n, d) < 0
        if not frente:
            if not doble_cara:
                continue
            n = -n
        b = 0.26 + 0.74 * max(0.0, float(np.dot(n, LUZ))) ** 0.85
        out.append((float(np.dot(P.mean(axis=0), d)),
                    np.column_stack([P @ ex, P @ ey]), b))
    out.sort(key=lambda r: -r[0])
    return out


# ============================================================================
# 6. LÁMINA DE PROPORCIONES — estudio de siluetas
#
# Deliberadamente SIN sombreado. Una superficie lofteada sin creases, sombreada,
# miente: parece jabón y no deja juzgar nada. La silueta plana es la herramienta
# que usa un diseñador para decidir proporción, y aquí es además exacta — la unión
# de los triángulos proyectados ES el contorno, sin aproximar.
# ============================================================================
import matplotlib                                                   # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                     # noqa: E402
from matplotlib.collections import PolyCollection                   # noqa: E402

FONDO, TINTA, TENUE = "#0d1117", "#c9d1d9", "#6e7681"
C_CUERPO = "#ced5dd"
C_PUERTA = "#e8a35c"
C_VIDRIO = "#5b6673"
C_LLANTA = "#20262e"
C_RIN = "#48515c"
C_PILOTO = "#3f8ddb"
C_HOY = "#262c35"
C_COTA = "#7d8590"


def silueta(ax, tris, cam, color, z=1, alpha=1.0):
    """Pinta la unión de los triángulos proyectados. Sin antialias y con el borde del
    mismo color: si no, las costuras entre triángulos dibujan una cuadrícula."""
    if not tris:
        return
    _, ex, ey = base_camara(cam)
    polis = [np.column_stack([np.array(t) @ ex, np.array(t) @ ey]) for t in tris]
    ax.add_collection(PolyCollection(polis, facecolors=color, edgecolors=color,
                                     linewidths=0.5, antialiased=False,
                                     zorder=z, alpha=alpha))


def encuadre(ax, tris_list, cam, mx=0.05, my=0.14):
    _, ex, ey = base_camara(cam)
    P = np.array([p for tris in tris_list for t in tris for p in t], float)
    u, v = P @ ex, P @ ey
    ax.set_xlim(u.min() - np.ptp(u) * mx, u.max() + np.ptp(u) * mx)
    ax.set_ylim(v.min() - np.ptp(v) * my, v.max() + np.ptp(v) * my)
    ax.set_aspect("equal")
    ax.axis("off")


def titulo(ax, t, sub=""):
    ax.set_title(t, color=TINTA, fontsize=11.5, pad=7, loc="left")
    if sub:
        ax.text(0.0, -0.025, sub, transform=ax.transAxes, color=TENUE, fontsize=8.8,
                va="top", ha="left")


def cota_h(ax, x0, x1, y, txt, color=C_COTA):
    ax.annotate("", (x0, y), (x1, y),
                arrowprops=dict(arrowstyle="<->", color=color, lw=0.9, shrinkA=0, shrinkB=0))
    ax.text((x0 + x1) / 2, y + 0.022, txt, color=color, fontsize=8.2, ha="center",
            va="bottom", family="monospace")


def cota_v(ax, x, y0, y1, txt, color=C_COTA):
    ax.annotate("", (x, y0), (x, y1),
                arrowprops=dict(arrowstyle="<->", color=color, lw=0.9, shrinkA=0, shrinkB=0))
    ax.text(x + 0.03, (y0 + y1) / 2, txt, color=color, fontsize=8.2, ha="left",
            va="center", family="monospace", rotation=90)


def barras_proporcion(ax, titulo_txt, valor, casos, objetivo):
    """Barras horizontales comparando una razón contra referencias conocidas."""
    ax.set_facecolor(FONDO)
    nombres = [c[0] for c in casos]
    vals = [c[1] for c in casos]
    cols = [c[2] for c in casos]
    y = np.arange(len(casos))
    ax.barh(y, vals, color=cols, height=0.62)
    ax.axvline(objetivo, color="#f0a868", lw=1.2, ls="--", alpha=0.8)
    for i, v in enumerate(vals):
        ax.text(v + max(vals) * 0.015, i, f"{v:.2f}", va="center", color=TINTA,
                fontsize=8.6, family="monospace")
    ax.set_yticks(y)
    ax.set_yticklabels(nombres, color=TENUE, fontsize=8.6)
    ax.invert_yaxis()
    ax.set_xlim(0, max(vals) * 1.16)
    ax.tick_params(axis="x", colors=TENUE, labelsize=8)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(titulo_txt, color=TINTA, fontsize=10.5, pad=6, loc="left")


# silueta lateral de la carrocería anterior, para comparar (de exportar_carro_3d.py)
EST_HOY = [(0.00, 0.34, 0.30, 0.42), (0.22, 0.56, 0.17, 0.52), (0.55, 0.80, 0.13, 0.60),
           (0.85, 0.76, 0.12, 0.68), (1.10, 0.74, 0.12, 0.78), (1.34, 0.72, 0.12, 1.04),
           (1.70, 0.74, 0.12, 1.10), (2.02, 0.76, 0.12, 1.09), (2.35, 0.80, 0.13, 0.92),
           (2.68, 0.81, 0.15, 0.72), (3.00, 0.52, 0.24, 0.54)]


def y_techo(x):
    return float(np.interp(x, [e[0] for e in EST], [e[6] for e in EST]))


# Maniquí de 1.75 m sentado con el respaldo reclinado, en perfil. Se dibuja como
# trazo y no como sólido: en un plano de paquete el ocupante se ve A TRAVÉS de la
# carrocería, que es justo para lo que sirve.
MANIQUI = dict(
    cadera=(1.900, 0.345), hombro=(2.005, 0.742), cabeza=(1.958, 0.862), r_cabeza=0.104,
    rodilla=(1.560, 0.402), tobillo=(1.312, 0.268), punta=(1.232, 0.238))


def dibujar_maniqui(ax, m=MANIQUI, color=C_PILOTO, z=6):
    tramos = [(m["cadera"], m["hombro"]), (m["cadera"], m["rodilla"]),
              (m["rodilla"], m["tobillo"]), (m["tobillo"], m["punta"])]
    for a, b in tramos:
        ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=7.5, solid_capstyle="round",
                alpha=0.85, zorder=z)
    ax.add_patch(plt.Circle(m["cabeza"], m["r_cabeza"], color=color, alpha=0.85, zorder=z))
    top = m["cabeza"][1] + m["r_cabeza"]
    ax.plot([m["cabeza"][0] - 0.17, m["cabeza"][0] + 0.30], [top, top],
            color=color, lw=0.9, ls=(0, (4, 3)), alpha=0.8, zorder=z)
    return top


def seccion_puerta(x, lado=+1):
    """Puntos de la sección de la puerta en la estación x (para el diagrama de giro)."""
    media = [recortar_pasos(p) for p in seccion(interp_est(x))]
    r = rango_puerta(x, media)
    if not r:
        return None
    return [(p[1], lado * p[2]) for p in media[r[0]:r[1] + 1]]


def girar_2d(pts, pivote, grados):
    a = np.radians(grados)
    ca, sa = np.cos(a), np.sin(a)
    py, pz = pivote
    return [(py + (y - py) * ca - (z - pz) * sa,
             pz + (y - py) * sa + (z - pz) * ca) for (y, z) in pts]


def eje_bisagra(lado=+1):
    """Recta de la bisagra de gaviota: el riel del espinazo, de la cabecera al arco."""
    p0 = np.array([X_HDR, y_techo(X_HDR), lado * Z_ESPINAZO])
    p1 = np.array([X_ARCO, y_techo(X_ARCO), lado * Z_ESPINAZO])
    u = p1 - p0
    return p0, u / np.linalg.norm(u)


def exportar_visor(nx=116, n_lob=32):
    """Geometría indexada para el visor three.js: cuerpo y las dos puertas, cada uno
    con sus grupos de material.

    Dos decisiones que importan:
      · INDEXADA — la piel es una rejilla, así que cada vértice lo comparten 6
        triángulos. Como sopa de triángulos pesaba 3.7 MB; indexada, ~0.6 MB.
      · Las NORMALES se promedian sobre la superficie completa (cuerpo + puertas
        cerradas) y sólo después se reparten. Calculadas por grupo, cada cambio de
        material dejaría una costura dura — que es justo lo que hacía ver la
        carrocería facetada.
    """
    xs = np.linspace(EST[0][0], EST[-1][0], nx)
    anillos = []
    for x in xs:
        media = [recortar_pasos(p) for p in seccion(interp_est(x), n_lob, n_lob)]
        anillos.append(media + [(px, py, -pz) for (px, py, pz) in reversed(media[1:-1])])
    n_media = len(anillos[0]) // 2 + 1
    n_ring = len(anillos[0])
    marca = celdas(xs, anillos, n_media)

    # normales suaves: se acumulan por vértice de la rejilla
    acum = [np.zeros(3) for _ in range(nx * n_ring)]
    def vi(i, k):
        return i * n_ring + (k % n_ring)
    for i in range(nx - 1):
        for k in range(n_ring):
            A, B = anillos[i][k], anillos[i + 1][k]
            Cc, D = anillos[i + 1][(k + 1) % n_ring], anillos[i][(k + 1) % n_ring]
            n = np.cross(np.array(B) - np.array(A), np.array(Cc) - np.array(A))
            ln = np.linalg.norm(n)
            if ln < 1e-12:
                continue
            n /= ln
            for idx in (vi(i, k), vi(i + 1, k), vi(i + 1, k + 1), vi(i, k + 1)):
                acum[idx] += n

    def construir(quiere):
        """quiere(i,k) -> nombre de material, o None si la celda no es de esta pieza."""
        vmap, pos, nor, grupos = {}, [], [], {}
        def v(i, k):
            key = (i, k % n_ring)
            if key not in vmap:
                vmap[key] = len(pos) // 3
                p = anillos[i][k % n_ring]
                q = acum[vi(i, k)]
                lq = np.linalg.norm(q)
                q = q / lq if lq > 1e-9 else np.array([0.0, 1.0, 0.0])
                pos.extend(round(float(c), 4) for c in p)
                nor.extend(round(float(c), 4) for c in q)
            return vmap[key]
        for i in range(nx - 1):
            for k in range(n_ring):
                m = quiere(i, k)
                if not m:
                    continue
                a, b, c, d = v(i, k), v(i + 1, k), v(i + 1, k + 1), v(i, k + 1)
                grupos.setdefault(m, []).extend([a, b, c, a, c, d])
        return pos, nor, grupos

    def mat_celda(i, k):
        return material(float(xs[i]), anillos[i][k % n_ring])

    piezas = {}
    pos, nor, gr = construir(lambda i, k: None if marca.get((i, k)) else mat_celda(i, k))
    # tapas de nariz y cola: abanico desde el centro del anillo
    for i_an, invertir in ((0, False), (nx - 1, True)):
        c = np.mean(np.array(anillos[i_an]), axis=0)
        ic = len(pos) // 3
        pos.extend(round(float(q), 4) for q in c)
        nx_, ny_ = (-1.0, 0.0) if i_an == 0 else (1.0, 0.0)
        nor.extend([round(nx_, 4), round(ny_, 4), 0.0])
        base = len(pos) // 3
        for k in range(n_ring):
            p = anillos[i_an][k]
            pos.extend(round(float(q), 4) for q in p)
            nor.extend([round(nx_, 4), round(ny_, 4), 0.0])
        for k in range(n_ring):
            m = material(float(xs[i_an]), anillos[i_an][k])
            a, b = base + k, base + (k + 1) % n_ring
            gr.setdefault(m, []).extend([ic, b, a] if not invertir else [ic, a, b])
    piezas["cuerpo"] = {"pos": pos, "nor": nor, "grupos": gr}

    for g, lado in (("pi", +1), ("pd", -1)):
        pos, nor, gr = construir(
            lambda i, k, g=g: mat_celda(i, k) if marca.get((i, k)) == g else None)
        p0, u = eje_bisagra(lado)
        piezas[g] = {"pos": pos, "nor": nor, "grupos": gr,
                     "eje": [round(float(c), 4) for c in list(p0) + list(u)],
                     "lado": lado}
    return piezas


def envolvente_puerta(n_x=48, n_ang=46):
    """Punto más alto y más lateral que alcanza la puerta en TODO el giro y en TODAS
    las estaciones. El máximo lateral no ocurre con la puerta abierta del todo sino a
    media apertura — por eso hay que barrer el ángulo y no evaluar solo la posición
    final."""
    alto = lateral = 0.0
    for x in np.linspace(X_PUERTA_F + 0.02, X_PUERTA_T - 0.02, n_x):
        p0 = seccion_puerta(x, +1)
        if not p0:
            continue
        piv = (y_techo(x), Z_ESPINAZO)
        for ang in np.linspace(0, 90, n_ang):
            g = girar_2d(p0, piv, -ang)
            alto = max(alto, max(q[0] for q in g))
            lateral = max(lateral, max(abs(q[1]) for q in g))
    return alto, lateral


ALTO_ABIERTA, ANCHO_BARRIDO = envolvente_puerta()


def linea_corte_puerta():
    """Contorno del hueco de la puerta en proyección lateral, analítico (no muestreado
    de la malla: así el trazo sale limpio y es la intención de diseño, no su pixelado)."""
    p = []
    for t in np.linspace(0, 1, 40):                      # pilar A
        p.append((X_PUERTA_F + (X_HDR - X_PUERTA_F) * t,
                  Y_ESTRIBO + (y_techo(X_HDR) - Y_ESTRIBO) * t ** 1.55))
    for t in np.linspace(0, 1, 30):                      # espinazo
        x = X_HDR + (X_ARCO - X_HDR) * t
        p.append((x, y_techo(x)))
    for t in np.linspace(0, 1, 40):                      # arco
        p.append((X_ARCO + (X_PUERTA_T - X_ARCO) * t,
                  y_techo(X_ARCO) - (y_techo(X_ARCO) - Y_ESTRIBO) * t ** 0.70))
    p.append((X_PUERTA_F, Y_ESTRIBO))
    return np.array(p)


def verificar():
    """Mide el modelo contra la lámina y escupe el error en mm. Sin ojímetro.

    La referencia viene normalizada por batalla con el eje delantero en 0, así que se
    lleva a metros con la batalla REAL. Lo que se compara es lo que la lámina de verdad
    define: los voladizos, la envolvente y la línea de techo. El ancho NO sale de aquí
    —la vista lateral no lo da— y por eso no se reporta: sale de la cenital, y sigue
    abierto.
    """
    x_ref = np.array(_SIL["x"]) * BATALLA + EJE_DEL
    y_ref = np.array(_SIL["techo"]) * BATALLA

    print("\n    VERIFICACION contra ref/silueta-referencia.json")
    print(f"    {'cota':<18}{'lamina':>9}{'modelo':>9}{'error mm':>10}")
    for nombre, ref, mod in (
            ("voladizo delantero", _SIL["voladizo_del"] * BATALLA, EJE_DEL - X_MORRO),
            ("voladizo trasero", _SIL["voladizo_tras"] * BATALLA, X_COLA - EJE_TRAS),
            ("largo", _SIL["largo_sobre_batalla"] * BATALLA, LARGO),
            ("alto", _SIL["alto_sobre_batalla"] * BATALLA, ALTO)):
        print(f"    {nombre:<18}{ref:>9.3f}{mod:>9.3f}{(mod - ref) * 1000:>+10.0f}")

    # Línea de techo: solo donde las dos existen, y en el mismo marco métrico.
    # MARGEN: los últimos milímetros de la silueta medida son basura de borde del
    # recorte — el "techo" salta a 1.05 m en la mera cola, más alto que la cabina, que
    # es geométricamente imposible. Se descartan en vez de dejarlos envenenar el RMS.
    m = (x_ref >= X_MORRO + MARGEN_REF) & (x_ref <= X_COLA - MARGEN_REF)
    err = np.array([y_techo(float(x)) for x in x_ref[m]]) - y_ref[m]
    k = int(np.argmax(np.abs(err)))
    print(f"    linea de techo    RMS {np.sqrt((err**2).mean())*1000:6.0f} mm   "
          f"max {err[k]*1000:+.0f} mm en x={x_ref[m][k]:.2f}  (n={m.sum()}, "
          f"{MARGEN_REF*1000:.0f} mm de margen descartados por borde)")
    print("    ancho: la vista lateral no lo define - sale de la cenital, sigue abierto")


def main():
    xs, anillos, n_media = malla()
    marca = celdas(xs, anillos, n_media)
    sup = superficies(xs, anillos, marca)
    cuerpo = [t for (g, m), ts in sup.items() if g == "cuerpo" for t in ts]
    pi = [t for (g, m), ts in sup.items() if g == "pi" for t in ts]
    pd = [t for (g, m), ts in sup.items() if g == "pd" for t in ts]

    EJES = ((EJE_DEL, R_DEL, Z_RUEDA_DEL), (EJE_TRAS, R_TRAS, Z_RUEDA_TRAS))
    ruedas = [t for (xa, R, zc) in EJES for lado in (+1, -1) for t in rueda(xa, R, zc, lado)]
    rines = [t for (xa, R, zc) in EJES for lado in (+1, -1) for t in rin(xa, R, zc, lado)]
    pilotos = piloto(+0.30) + piloto(-0.30)
    todo = cuerpo + pi + pd + ruedas

    fig = plt.figure(figsize=(20.0, 12.2), facecolor=FONDO)
    gs = fig.add_gridspec(3, 6, hspace=0.30, wspace=0.30,
                          left=0.030, right=0.975, top=0.895, bottom=0.055)
    fig.text(0.030, 0.955, "CARROCERÍA v2 — ESTUDIO DE PROPORCIONES", color="#f0f6fc",
             fontsize=21, fontweight="bold")
    fig.text(0.030, 0.925,
             f"Escenario D · {LARGO:.2f} × {ANCHO:.2f} × {ALTO:.2f} m · batalla y trocha "
             "SIN TOCAR · gaviota profunda · siluetas exactas, sin sombreado que engañe",
             color=TENUE, fontsize=10.8)

    # ---- VISTA LATERAL (la vista que decide la proporción) --------------------
    ax = fig.add_subplot(gs[0:2, 0:4])
    LAT = (0, 0, 1)
    hoy = np.array([(e[0], e[3]) for e in EST_HOY] + [(e[0], e[2]) for e in EST_HOY][::-1])
    ax.fill(hoy[:, 0], hoy[:, 1], color=C_HOY, zorder=0)
    ax.text(0.06, 1.17, "silueta de hoy: 3.00 × 1.62 × 1.10", color="#5a6472",
            fontsize=8.8, ha="left", fontweight="bold", zorder=1)
    silueta(ax, cuerpo + pi + pd, LAT, C_CUERPO, z=2)
    silueta(ax, ruedas, LAT, C_LLANTA, z=3)
    silueta(ax, rines, LAT, C_RIN, z=4)
    y_cabeza = dibujar_maniqui(ax)
    ax.text(MANIQUI["cabeza"][0] + 0.31, y_cabeza, f"  cabeza {y_cabeza*1000:.0f} mm  ·  "
            f"{(Y_ARCO-y_cabeza)*1000:.0f} mm bajo el arco", color=C_PILOTO, fontsize=7.8,
            va="center", ha="left", zorder=7)
    lp = linea_corte_puerta()
    ax.plot(lp[:, 0], lp[:, 1], color="#c25a10", lw=2.0, zorder=6)
    cin = np.array(Y_CINTURA)
    ax.plot(cin[:, 0], cin[:, 1], color=C_VIDRIO, lw=1.3, ls=(0, (5, 3)), zorder=6)
    for (px, py, et) in ((X_COWL, Y_COWL, "pilar A"), (X_HDR, Y_HDR, "cabecera"),
                         (X_ARCO, Y_ARCO, "arco ppal")):
        ax.plot([px], [py], "o", ms=5, color="#f0a868", zorder=7)
        ax.text(px, py + 0.045, et, color="#f0a868", fontsize=7.8, ha="center", zorder=7)
    ax.axhline(0, color=C_COTA, lw=1.0, zorder=1)
    cota_h(ax, X_MORRO, X_COLA, -0.135, f"largo {LARGO:.2f} m")
    cota_h(ax, EJE_DEL, EJE_TRAS, -0.055, f"batalla {EJE_TRAS-EJE_DEL:.2f} m")
    cota_h(ax, X_MORRO, EJE_DEL, -0.215, f"voladizo {VOL_DEL*1000:.0f}")
    cota_h(ax, EJE_TRAS, X_COLA, -0.215, f"voladizo {VOL_TRAS*1000:.0f}")
    cota_v(ax, X_COLA + 0.10, 0, ALTO, f"alto {ALTO:.2f} m")
    encuadre(ax, [todo], LAT, mx=0.055, my=0.20)
    titulo(ax, "VISTA LATERAL",
           "naranja = corte de la puerta de gaviota · punteado = cintura de cristal · "
           "azul = piloto de 1.75 m · ámbar = nodos reales del chasis")

    # ---- PLANO DE FORMAS (secciones superpuestas) ------------------------------
    # Como el plano de formas de un casco: adelante a la derecha, atrás a la izquierda.
    # Dice mucho más de la superficie que una silueta frontal, que sale cacerola.
    ax = fig.add_subplot(gs[0, 4:6])
    ax.set_facecolor(FONDO)
    DEL_ = [(0.30, "#3d5a80"), (0.55, "#5680ad"), (0.95, "#7aa5cc"), (1.45, "#a9cbe8")]
    TRA_ = [(3.10, "#7d4a2e"), (2.68, "#b0663d"), (2.30, "#d68b52"), (1.90, "#f0b077")]
    for lista, signo in ((DEL_, +1), (TRA_, -1)):
        for x, col in lista:
            m = [recortar_pasos(p) for p in seccion(interp_est(x))]
            ax.plot([signo * p[2] for p in m], [p[1] for p in m], color=col, lw=1.5)
    for signo, R, zc in ((+1, R_DEL, Z_RUEDA_DEL), (-1, R_TRAS, Z_RUEDA_TRAS)):
        for zz in (zc - ANCHO_LL / 2, zc + ANCHO_LL / 2):
            ax.plot([signo * zz] * 2, [0, 2 * R], color=C_LLANTA, lw=1.2)
        ax.plot([signo * (zc - ANCHO_LL / 2), signo * (zc + ANCHO_LL / 2)],
                [2 * R, 2 * R], color=C_LLANTA, lw=1.2)
    ax.axhline(0, color=C_COTA, lw=1.0)
    ax.axvline(0, color="#30363d", lw=0.9, ls=(0, (4, 4)))
    ax.text(0.62, 1.075, "ADELANTE", color="#a9cbe8", fontsize=8.4, ha="center")
    ax.text(-0.62, 1.075, "ATRÁS", color="#f0b077", fontsize=8.4, ha="center")
    ax.set_xlim(-1.02, 1.02)
    ax.set_ylim(-0.10, 1.18)
    ax.set_aspect("equal")
    ax.axis("off")
    titulo(ax, "PLANO DE FORMAS  (secciones)",
           f"W/H {ANCHO/ALTO:.2f} · la salpicadera ya tapa la llanta (41 mm por lado)")

    # ---- CENITAL --------------------------------------------------------------
    ax = fig.add_subplot(gs[1, 4:6])
    CEN = (0, -1, 0)
    silueta(ax, cuerpo, CEN, C_CUERPO, z=2)
    silueta(ax, pi + pd, CEN, C_PUERTA, z=3)
    silueta(ax, ruedas, CEN, C_LLANTA, z=1)
    encuadre(ax, [todo], CEN, my=0.10)
    titulo(ax, "VISTA CENITAL",
           f"naranja = puertas · lomo fijo de {2*Z_ESPINAZO*100:.0f} cm entre ellas")

    # ---- DIAGRAMA DE GIRO DE LA PUERTA ----------------------------------------
    ax = fig.add_subplot(gs[2, 0:2])
    ax.set_facecolor(FONDO)
    X_SEC = 1.750
    sec = [recortar_pasos(p) for p in seccion(interp_est(X_SEC))]
    perfil = [(-p[2], p[1]) for p in reversed(sec)] + [(p[2], p[1]) for p in sec]
    ax.plot([p[0] for p in perfil], [p[1] for p in perfil], color="#48515c", lw=1.4)
    piv = (y_techo(X_SEC), Z_ESPINAZO)
    for ang, lw, al in ((0, 2.4, 0.85), (36, 1.4, 0.40), (72, 2.4, 0.85), (90, 1.4, 0.40)):
        for lado in (+1, -1):
            p0 = seccion_puerta(X_SEC, lado)
            if not p0:
                continue
            g = girar_2d(p0, (piv[0], lado * piv[1]), -ang * lado)
            ax.plot([q[1] for q in g], [q[0] for q in g], color=C_PUERTA, lw=lw, alpha=al)
        ax.plot([lado * piv[1]], [piv[0]], "o", ms=4.5, color="#f0f6fc", zorder=5)
    # envolvente barrida por la esquina inferior de la puerta (la que decide el claro)
    esq = seccion_puerta(X_SEC, +1)[0]
    arco = [girar_2d([esq], (piv[0], piv[1]), -a)[0] for a in range(0, 95, 3)]
    for s in (+1, -1):
        ax.plot([s * q[1] for q in arco], [q[0] for q in arco], color="#4b5563",
                lw=0.9, ls=(0, (3, 3)))
    ax.axhline(0, color=C_COTA, lw=1.0)
    ax.axhline(2.10, color="#f85149", lw=1.2, ls=(0, (6, 4)))
    ax.text(-1.55, 2.15, "techo de cochera 2.10 m", color="#f85149", fontsize=8.4)
    ax.annotate("", (1.30, 0), (1.30, ALTO_ABIERTA),
                arrowprops=dict(arrowstyle="<->", color=C_COTA, lw=0.9))
    ax.text(1.36, ALTO_ABIERTA / 2, f"{ALTO_ABIERTA*1000:.0f} mm abierta",
            color=C_COTA, fontsize=8.4, rotation=90, va="center", family="monospace")
    ax.annotate("", (SEMI, 0.10), (ANCHO_BARRIDO, 0.10),
                arrowprops=dict(arrowstyle="<->", color="#f0a868", lw=1.1))
    ax.text(ANCHO_BARRIDO + 0.05, 0.10,
            f"barre {(ANCHO_BARRIDO-SEMI)*1000:.0f} mm\nafuera del costado",
            color="#f0a868", fontsize=8.2, va="center", family="monospace")
    ax.set_xlim(-1.62, 1.90)
    ax.set_ylim(-0.10, 2.32)
    ax.set_aspect("equal")
    ax.axis("off")
    titulo(ax, f"GIRO DE LA PUERTA  (sección en x={X_SEC:.2f} m)",
           "bisagra de pasador simple en el espinazo · cerrada, 36°, 72° y 90° · "
           "punteado = envolvente de la esquina baja")

    # ---- BARRAS DE PROPORCIÓN -------------------------------------------------
    ax = fig.add_subplot(gs[2, 2:4])
    barras_proporcion(ax, "LARGO / ALTO", LARGO / ALTO, [
        ("Alfa 33 Stradale", 4.01, "#30363d"), ("tu referencia (est.)", 3.97, "#30363d"),
        ("Lotus Elise S1", 3.32, "#30363d"),
        ("PROPUESTA", LARGO / ALTO, "#e8a35c"),
        ("carro de hoy", 2.73, C_HOY), ("Fiat 500", 2.40, "#30363d")], 3.32)
    ax = fig.add_subplot(gs[2, 4:6])
    barras_proporcion(ax, "ANCHO / ALTO   (la estampa de frente)", ANCHO / ALTO, [
        ("Alfa 33 Stradale", 1.73, "#30363d"), ("tu referencia (est.)", 1.72, "#30363d"),
        ("PROPUESTA", ANCHO / ALTO, "#e8a35c"),
        ("Lotus Elise S1", 1.54, "#30363d"),
        ("carro de hoy", 1.47, C_HOY), ("Fiat 500", 1.09, "#30363d")], 1.73)

    out_png = os.path.join(HERE, "carroceria-proporciones.png")
    fig.savefig(out_png, dpi=112, facecolor=FONDO)
    plt.close(fig)

    out_json = os.path.join(HERE, "carroceria-superficie.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"superficies": {f"{g}|{m}": [[round(v, 4) for p in t for v in p]
                                                for t in ts] for (g, m), ts in sup.items()},
                   "cotas": {"largo": LARGO, "ancho": ANCHO, "alto": ALTO,
                             "z_espinazo": Z_ESPINAZO, "x_morro": X_MORRO,
                             "x_cola": X_COLA, "batalla": BATALLA,
                             "voladizo_del": VOL_DEL, "voladizo_tras": VOL_TRAS}},
                  f, separators=(",", ":"))

    print(f"OK  carroceria {LARGO:.2f} x {ANCHO:.2f} x {ALTO:.2f} m")
    print(f"    L/H {LARGO/ALTO:.2f}   W/H {ANCHO/ALTO:.2f}   rueda/H {2*R_TRAS/ALTO:.2f}")
    print(f"    triangulos: cuerpo {len(cuerpo)}  puertas {len(pi)}+{len(pd)}")
    verificar()
    print(f"OK  {out_png}")
    print(f"OK  {out_json}")


if __name__ == "__main__":
    main()


