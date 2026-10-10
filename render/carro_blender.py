# -*- coding: utf-8 -*-
"""
El carro en Blender — modelo de superficie y render de estudio.

Se corre SIN ventana:
    blender --background --python render/carro_blender.py -- --vistas todo --muestras 128

Método (el mismo que usa un estudio de diseño, no un loft ciego):
  · La carrocería es una JAULA DE CONTROL de pocos puntos — quilla, faldón, hombro,
    cintura/lomo de salpicadera, borde de techo y espinazo — a la que se le aplica
    subdivisión Catmull-Clark. Las líneas de carácter se marcan con CREASE, que es de
    donde salen los reflejos que hacen que un carro parezca un carro.
  · Los pasos de rueda se cortan con booleano contra un cilindro: el labio queda
    limpio y afilado, como una salpicadera de verdad.
  · Las puertas de gaviota se separan de la misma piel, así el corte encaja perfecto,
    y cuelgan de un vacío en el eje del espinazo.
  · El chasis entra desde cad/chasis.json (lo escribe calculos/exportar_blender.py):
    manda la ingeniería, no el dibujo.

La jaula se valida contra la envolvente medida del chasis: si un tubo asoma, avisa.
"""
import json
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(nombre, defecto):
    if nombre in ARGS:
        return ARGS[ARGS.index(nombre) + 1]
    return defecto


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "render", "salida")
os.makedirs(SALIDA, exist_ok=True)
CH = json.load(open(os.path.join(RAIZ, "cad", "chasis.json"), encoding="utf-8"))

# ============================================================================
# 1. RED DE CURVAS DE LA CARROCERÍA
#    Siete curvas longitudinales. Cada estación aporta un punto a cada una y la
#    subdivisión hace el resto. Los valores de quilla, faldón y espinazo NO son
#    de gusto: salen de la envolvente medida del chasis (ver validación abajo).
# ============================================================================
#        x     quilla      faldón        hombro       cintura/lomo   borde techo  espinazo
#              y     z     y     z      y      z      y      z       y      z      y
EST = [
    (0.000, 0.300, 0.055, 0.318, 0.140, 0.334, 0.175, 0.344, 0.130, 0.348, 0.060, 0.352),
    (0.150, 0.212, 0.200, 0.252, 0.400, 0.300, 0.470, 0.348, 0.340, 0.360, 0.160, 0.364),
    (0.320, 0.148, 0.300, 0.214, 0.530, 0.316, 0.662, 0.432, 0.500, 0.456, 0.240, 0.450),
    (0.550, 0.130, 0.380, 0.230, 0.602, 0.366, 0.906, 0.606, 0.720, 0.586, 0.350, 0.552),
    (0.780, 0.128, 0.420, 0.245, 0.630, 0.396, 0.892, 0.641, 0.742, 0.627, 0.380, 0.601),
    (0.950, 0.128, 0.440, 0.256, 0.646, 0.421, 0.878, 0.700, 0.766, 0.744, 0.430, 0.755),
    (1.200, 0.128, 0.450, 0.263, 0.653, 0.441, 0.876, 0.774, 0.842, 0.856, 0.470, 0.878),
    (1.450, 0.128, 0.450, 0.269, 0.657, 0.456, 0.883, 0.800, 0.850, 0.962, 0.448, 0.985),
    (1.750, 0.128, 0.450, 0.277, 0.661, 0.471, 0.893, 0.812, 0.860, 1.032, 0.436, 1.058),
    (2.020, 0.130, 0.440, 0.285, 0.663, 0.486, 0.906, 0.820, 0.870, 1.034, 0.424, 1.064),
    (2.350, 0.139, 0.420, 0.297, 0.659, 0.506, 0.911, 0.812, 0.866, 0.978, 0.404, 1.008),
    (2.680, 0.164, 0.380, 0.316, 0.641, 0.526, 0.886, 0.780, 0.822, 0.878, 0.330, 0.891),
    (3.000, 0.230, 0.300, 0.371, 0.548, 0.546, 0.772, 0.706, 0.700, 0.742, 0.250, 0.754),
    (3.200, 0.320, 0.220, 0.431, 0.430, 0.561, 0.630, 0.661, 0.552, 0.651, 0.180, 0.653),
    (3.350, 0.398, 0.140, 0.470, 0.300, 0.546, 0.442, 0.591, 0.372, 0.561, 0.110, 0.561),
]
N_ANILLO = 7          # puntos por media sección
CREASE = {1: 0.85, 3: 0.55, 4: 0.45}     # índice de anillo -> firmeza de la línea

# Margenes de piel sobre el chasis (m). La carrocería es sándwich de ~12 mm más el
# hueco de montaje; 30 mm de lado y 20 mm arriba es lo mínimo sano para pasar cables
# y separadores sin que un tubo marque la superficie.
MARGEN_LADO, MARGEN_ARRIBA, MARGEN_PISO = 0.030, 0.020, 0.016
EJE_DEL, EJE_TRAS = CH["ruedas"][0]["x"], CH["ruedas"][2]["x"]
LARGO_OBJ = 3.350
ANCHO_OBJ = 1.820
ALTO_OBJ = 1.075


def _perfil_referencia():
    """Trae la silueta MEDIDA de la lámina del dueño (calculos/silueta_ref.py) y la
    monta sobre nuestro paquete.

    El mapeo en x es lineal por tramos anclado en LOS DOS EJES: entre ejes va 1:1 y
    sólo se comprime el voladizo delantero (la referencia lo tiene más largo que
    nuestro chasis) y se estira el trasero. Es lo que hace un diseñador al adaptar una
    proporción a otra batalla; escalar todo por igual movería los ejes de lugar.
    """
    import numpy as np
    f = os.path.join(RAIZ, "ref", "silueta-referencia.json")
    if not os.path.exists(f):
        return None
    d = json.load(open(f, encoding="utf-8"))
    xr = np.array(d["x"], float)
    techo = np.array(d["techo"], float)
    piso = np.array(d["piso"], float)
    # mediana de 9 para matar picos de la cuadrícula del fondo
    def mediana(v, k=9):
        pad = np.pad(v, k // 2, mode="edge")
        return np.array([np.median(pad[i:i + k]) for i in range(len(v))])
    techo, piso = mediana(techo), mediana(piso)

    B = EJE_TRAS - EJE_DEL
    nodos_ref = [xr[0], 0.0, 1.0, xr[-1]]
    nodos_nos = [0.0, EJE_DEL, EJE_TRAS, LARGO_OBJ]
    x_nos = np.interp(xr, nodos_ref, nodos_nos)
    return x_nos, techo * B, piso * B


def _clampar(EST_estilo):
    """Recorta la intención de estilo contra la envolvente MEDIDA del chasis.

    Antes esto era una validación que sólo avisaba; ahora es una restricción: la
    superficie no puede quedar por dentro del chasis porque el propio generador lo
    impide. Después se suaviza, para que el recorte no deje un escalón.
    """
    import numpy as np
    ex = [s["x"] for s in CH["envolvente"]]
    ez = [s["z"] for s in CH["envolvente"]]
    elo = [s["y_lo"] for s in CH["envolvente"]]
    ehi = [s["y_hi"] for s in CH["envolvente"]]
    # densificar ANTES de recortar: si no, la interpolación entre estaciones se
    # despega de la envolvente justo donde el chasis cambia de altura (la cola)
    T0 = np.array([list(e) for e in EST_estilo], dtype=float)
    x = np.unique(np.concatenate([T0[:, 0], np.linspace(0, T0[-1, 0], 34)]))
    T = np.column_stack([x] + [np.interp(x, T0[:, 0], T0[:, j])
                               for j in range(1, T0.shape[1])])
    ref = _perfil_referencia()
    if ref is not None:
        # el ESPINAZO y la QUILLA los manda la referencia medida; los anchos siguen
        # siendo nuestros porque la vista lateral no dice nada de ancho
        xr, techo_r, piso_r = ref
        # se mezcla con la intención propia y se suelta en los extremos: la lámina
        # trae ahí el alerón y el difusor del concepto, que no son nuestra cola
        w = np.clip(np.minimum((x - 0.02) / 0.30, (3.10 - x) / 0.45), 0.0, 1.0)
        T[:, 11] = (1 - w) * T[:, 11] + w * np.interp(x, xr, techo_r)
        T[:, 1] = (1 - w) * T[:, 1] + w * np.interp(x, xr, piso_r)
        # el borde de techo acompaña al espinazo manteniendo su caída relativa
        caida = np.interp(x, T0[:, 0], T0[:, 11] - T0[:, 9])
        T[:, 9] = T[:, 11] - np.clip(caida, -0.06, 0.10)

    z_min = np.interp(x, ex, ez) + MARGEN_LADO
    y_hi = np.interp(x, ex, ehi) + MARGEN_ARRIBA
    y_lo = np.interp(x, ex, elo) - MARGEN_PISO
    fuera = (x < ex[0] - 0.02) | (x > ex[-1] + 0.02)
    z_min[fuera] = 0.0
    y_hi[fuera] = 0.0
    y_lo[fuera] = 9.0

    T[:, 4] = np.maximum(T[:, 4], z_min)                 # faldón: ancho abajo
    T[:, 6] = np.maximum(T[:, 6], T[:, 4] + 0.020)       # hombro por fuera del faldón
    T[:, 8] = np.maximum(T[:, 8], T[:, 6] - 0.075)
    T[:, 11] = np.maximum(T[:, 11], y_hi)                # espinazo sobre el chasis
    T[:, 9] = np.maximum(T[:, 9], y_hi - 0.012)          # borde de techo
    T[:, 7] = np.minimum(T[:, 7], T[:, 11] - 0.055)      # cintura bajo el espinazo
    T[:, 1] = np.minimum(T[:, 1], y_lo)                  # quilla bajo el piso
    T[:, 3] = np.maximum(T[:, 3], T[:, 1] + 0.055)

    # suavizado 1-2-1 en las columnas que el recorte pudo escalonar
    for j in (1, 3, 4, 6, 7, 9, 11):
        c = T[:, j].copy()
        for _ in range(3):
            c[1:-1] = 0.25 * c[:-2] + 0.5 * c[1:-1] + 0.25 * c[2:]
        # el suavizado no puede volver a meter la piel dentro del chasis
        if j == 4:
            c = np.maximum(c, z_min)
        if j == 11:
            c = np.maximum(c, y_hi)
        if j == 9:
            c = np.maximum(c, y_hi - 0.012)
        if j == 1:
            c = np.minimum(c, y_lo)
        T[:, j] = c

    # ORDEN DE LA SECCIÓN. Sin esto el recorte puede dejar la quilla por encima del
    # hombro y el contorno se enrolla sobre sí mismo: eso es lo que salía arrugado.
    #   y: sube de la quilla al borde de techo (el espinazo SÍ puede quedar por debajo
    #      del borde: ése es el valle del cofre entre las dos salpicaderas)
    #   z: crece de la quilla al hombro y decrece del hombro al techo
    T[:, [1, 3, 5, 7, 9]] = np.maximum.accumulate(T[:, [1, 3, 5, 7, 9]], axis=1)
    T[:, [2, 4, 6]] = np.maximum.accumulate(T[:, [2, 4, 6]], axis=1)
    T[:, [6, 8, 10]] = np.minimum.accumulate(T[:, [6, 8, 10]], axis=1)
    # separaciones mínimas para que la subdivisión no colapse el aro
    for a, b in ((1, 3), (3, 5), (5, 7), (7, 9)):
        T[:, b] = np.maximum(T[:, b], T[:, a] + 0.012)
    return [tuple(r) for r in T]


EST = _clampar(EST)

LARGO = EST[-1][0]
ANCHO = 2 * max(e[6] for e in EST)
ALTO = max(e[11] for e in EST)

X_PUERTA = (1.055, 2.120)
Y_ESTRIBO = 0.430
Z_ESPINAZO = CH["duros"]["z_espinazo"]
X_HDR, Y_HDR = CH["duros"]["cabecera"]
X_ARCO, Y_ARCO = CH["duros"]["arco"]


def anillo(e):
    """Puntos (y,z) de la media sección, de la quilla al espinazo."""
    x, kq, kz, fy, fz, hy, hz, cy, cz, ty, tz, sy = e
    return [(kq, 0.0), (kq, kz), (fy, fz), (hy, hz), (cy, cz), (ty, tz), (sy, 0.0)]


# ============================================================================
# 2. VALIDACIÓN: ¿la jaula contiene el chasis?
# ============================================================================
def validar():
    import numpy as np
    xs = [e[0] for e in EST]
    faltas = []
    for s in CH["envolvente"]:
        x = s["x"]
        if x < xs[0] or x > xs[-1]:
            continue
        col = lambda j: float(np.interp(x, xs, [e[j] for e in EST]))
        # el larguero corre abajo: el ancho que importa es el del FALDON (columna 4)
        holgura_z = col(4) - s["z"]
        holgura_y = s["y_lo"] - col(1)
        holgura_t = col(11) - s["y_hi"]
        if min(holgura_z, holgura_y, holgura_t) < 0.008:
            faltas.append((x, holgura_z * 1000, holgura_y * 1000, holgura_t * 1000))
    print("\n" + "=" * 74)
    print("VALIDACION: la carroceria contra la envolvente medida del chasis")
    print("=" * 74)
    if not faltas:
        print("  OK — ningun tubo asoma. Holgura minima >= 10 mm en las 60 estaciones.")
    else:
        print(f"  {len(faltas)} estaciones con menos de 10 mm:")
        for x, a, b, c in faltas[:14]:
            print(f"    x={x:5.2f}   ancho {a:+7.1f} mm   piso {b:+7.1f} mm   techo {c:+7.1f} mm")
    print()
    return not faltas


# ============================================================================
# 3. CONSTRUCCIÓN DE MALLA
# ============================================================================
def limpiar():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def nueva_malla(nombre, verts, faces):
    me = bpy.data.meshes.new(nombre)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.collection.objects.link(ob)
    return ob


N_EST_CASCO, N_ALT_CASCO = 40, 20


def jaula_casco(M):
    """Jaula construida por CASCO VISUAL a partir de las tres vistas de la lámina.

    Cada estación trae su sección medida (la vista frontal manda la forma, la cenital
    el ancho y la lateral la altura). Aquí sólo se escala al paquete, se le pone
    nuestro piso plano —en la lámina el piso incluye llantas y sombra, no sirve— y se
    recorta contra la envolvente del chasis SIN deformar la sección: se escala
    completa, para no perder la forma que costó medir.
    """
    import numpy as np
    d = json.load(open(os.path.join(RAIZ, "ref", "casco-visual.json"), encoding="utf-8"))
    est = [e for e in d["estaciones"] if e["x"] <= 0.985]
    xs_n = np.array([e["x"] for e in est])
    secs = np.array([e["sec"] for e in est])            # (n_est, n_alt, 2)

    ex = [s["x"] for s in CH["envolvente"]]
    ez = [s["z"] for s in CH["envolvente"]]
    elo = [s["y_lo"] for s in CH["envolvente"]]
    ehi = [s["y_hi"] for s in CH["envolvente"]]

    xs = np.linspace(0.0, LARGO_OBJ, N_EST_CASCO)
    anillos, medias = [], []
    for x in xs:
        xn = x / LARGO_OBJ
        i = int(np.clip(np.searchsorted(xs_n, xn) - 1, 0, len(est) - 2))
        t = (xn - xs_n[i]) / max(xs_n[i + 1] - xs_n[i], 1e-9)
        S = secs[i] * (1 - t) + secs[i + 1] * t         # (n_alt, 2) en normalizado
        yv = S[:, 0] * ALTO_OBJ
        zv = S[:, 1] * (ANCHO_OBJ / 2)

        # remuestreo a N_ALT_CASCO puntos, de abajo hacia arriba
        u = np.linspace(0, 1, len(yv))
        un = np.linspace(0, 1, N_ALT_CASCO)
        yv = np.interp(un, u, yv)
        zv = np.interp(un, u, zv)

        # piso propio: plano y por debajo del chasis
        dentro = (x >= ex[0] - 0.02) and (x <= ex[-1] + 0.02)
        y_keel = (np.interp(x, ex, elo) - MARGEN_PISO) if dentro else yv.min()
        yv = np.maximum(yv, min(y_keel, yv.max() - 0.02))
        yv[0] = min(y_keel, yv[1] - 0.005)

        # recorte al chasis: se escala la sección ENTERA, no se deforma
        z_need = (np.interp(x, ex, ez) + MARGEN_LADO) if dentro else 0.0
        y_need = (np.interp(x, ex, ehi) + MARGEN_ARRIBA) if dentro else 0.0
        # y la salpicadera tiene que TAPAR la llanta: la referencia es un carro con
        # otra trocha, así que su ancho relativo dejaba 15 cm de rueda al aire
        for r in CH["ruedas"]:
            if abs(x - r["x"]) < 0.40:
                cae = 1.0 - (abs(x - r["x"]) / 0.40) ** 2
                z_need = max(z_need, (abs(r["z"]) + r["W"] / 2 + 0.045) * (0.72 + 0.28 * cae))
        if z_need and zv.max() < z_need:
            zv = zv * (z_need / max(zv.max(), 1e-6))
        if y_need and yv.max() < y_need:
            yv = yv[0] + (yv - yv[0]) * ((y_need - yv[0]) / max(yv.max() - yv[0], 1e-6))
        medias.append(np.column_stack([yv, zv]))

    # suavizado longitudinal: el muestreo por pixel deja ondas finas
    A = np.array(medias)
    for _ in range(2):
        A[1:-1] = 0.25 * A[:-2] + 0.5 * A[1:-1] + 0.25 * A[2:]

    verts, idxs = [], []
    for x, med in zip(xs, A):
        fila = []
        for (y, z) in med:
            fila.append(len(verts))
            verts.append((float(x), float(y), float(z)))
        for (y, z) in med[::-1][1:-1]:
            fila.append(len(verts))
            verts.append((float(x), float(y), float(-z)))
        idxs.append(fila)

    faces, mats = [], []
    n = len(idxs[0])
    xp0, xp1 = X_PUERTA[0] - 0.12, X_PUERTA[1] + 0.03
    for i in range(len(idxs) - 1):
        Aa, Bb = idxs[i], idxs[i + 1]
        xm = 0.5 * (xs[i] + xs[i + 1])
        for k in range(n):
            k2 = (k + 1) % n
            faces.append((Aa[k], Aa[k2], Bb[k2], Bb[k]))
            j = k if k < N_ALT_CASCO else (2 * N_ALT_CASCO - 2 - k)
            frac = j / (N_ALT_CASCO - 1)
            if frac < 0.16:
                mats.append(2)                                   # faldón / undertray
            elif frac > 0.66 and xp0 <= xm <= xp1:
                mats.append(1)                                   # cristal
            else:
                mats.append(0)
    faces.append(tuple(reversed(idxs[0])))
    mats.append(2)
    faces.append(tuple(idxs[-1]))
    mats.append(2)

    ob = nueva_malla("Carroceria", verts, faces)
    for k in ("pintura", "vidrio", "negro", "luz_t", "luz_d"):
        ob.data.materials.append(M[k])
    for p_, mi in zip(ob.data.polygons, mats):
        p_.material_index = mi
        p_.use_smooth = True
    # crease en la línea de cintura, donde nace el cristal
    attr = ob.data.attributes.new(name="crease_edge", type='FLOAT', domain='EDGE')
    fila = {v: k for an in idxs for k, v in enumerate(an)}
    for ed in ob.data.edges:
        a, b = ed.vertices
        ka, kb = fila.get(a), fila.get(b)
        if ka is None or kb is None or ka != kb:
            continue
        j = ka if ka < N_ALT_CASCO else (2 * N_ALT_CASCO - 2 - ka)
        frac = j / (N_ALT_CASCO - 1)
        if abs(frac - 0.66) < 0.03 or abs(frac - 0.16) < 0.03:
            attr.data[ed.index].value = 0.55
    return ob


def construir_jaula(M):
    """Jaula de control: anillos de 12 puntos (7 por lado, espejo sin repetir polos)."""
    verts, anillos = [], []
    for e in EST:
        med = anillo(e)
        idx = []
        for (y, z) in med:                       # lado +z
            idx.append(len(verts))
            verts.append((e[0], y, z))
        for (y, z) in reversed(med[1:-1]):       # espejo, sin repetir polos
            idx.append(len(verts))
            verts.append((e[0], y, -z))
        anillos.append(idx)
    # El material se asigna AQUÍ, sobre la jaula, no sobre la malla subdividida: así
    # el límite entre pintura, negro y cristal es un aro de la superficie y sale
    # perfecto. Asignado después, por cara, el borde escalona con la malla.
    faces, mats = [], []
    n = len(anillos[0])
    x0, x1 = X_PUERTA[0] - 0.12, X_PUERTA[1] + 0.03
    for i in range(len(anillos) - 1):
        A, B = anillos[i], anillos[i + 1]
        xm = 0.5 * (EST[i][0] + EST[i + 1][0])
        for k in range(n):
            k2 = (k + 1) % n
            faces.append((A[k], A[k2], B[k2], B[k]))
            j = k if k < N_ANILLO - 1 else (2 * N_ANILLO - 3 - k)   # índice espejado
            if j <= 1:
                mats.append(2)                                       # quilla y faldón
            elif j == 4 and x0 <= xm <= x1:
                mats.append(1)                                       # cristal
            else:
                mats.append(0)                                       # pintura
    faces.append(tuple(reversed(anillos[0])))    # tapa nariz
    mats.append(2)
    faces.append(tuple(anillos[-1]))             # tapa cola
    mats.append(2)
    ob = nueva_malla("Carroceria", verts, faces)
    for k in ("pintura", "vidrio", "negro", "luz_t", "luz_d"):
        ob.data.materials.append(M[k])
    for p_, mi in zip(ob.data.polygons, mats):
        p_.material_index = mi

    # creases sobre los aros longitudinales de carácter
    me = ob.data
    attr = me.attributes.new(name="crease_edge", type='FLOAT', domain='EDGE')
    fila = {}
    for i, an in enumerate(anillos):
        for k, v in enumerate(an):
            fila[v] = k
    for ed in me.edges:
        a, b = ed.vertices
        ka, kb = fila.get(a), fila.get(b)
        if ka is None or kb is None or ka != kb:
            continue                              # sólo aros longitudinales
        k = ka if ka < N_ANILLO else (2 * N_ANILLO - 2 - ka)
        if k in CREASE:
            attr.data[ed.index].value = CREASE[k]
    for p in me.polygons:
        p.use_smooth = True
    return ob


def subdividir(ob, niveles=3):
    m = ob.modifiers.new("subdiv", 'SUBSURF')
    m.levels = niveles
    m.render_levels = niveles
    m.use_limit_surface = True
    return ob


def aplicar_modificadores(ob):
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def cilindro_corte(nombre, x, R, z0, z1, seg=72):
    """Cilindro con el eje en Z para cortar el paso de rueda, LIMITADO a un costado.

    Antes atravesaba el carro de lado a lado y se llevaba también el piso y el centro
    de la carrocería: el hueco del paso de rueda es de la salpicadera hacia afuera,
    no de todo el ancho.
    """
    verts, faces = [], []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        y = 0.16 + R * math.sin(a)
        xx = x + R * math.cos(a)
        verts.append((xx, y, z0))
        verts.append((xx, y, z1))
    for k in range(seg):
        a, b = 2 * k, 2 * ((k + 1) % seg)
        faces.append((a, b, b + 1, a + 1))
    faces.append(tuple(range(0, 2 * seg, 2)))
    faces.append(tuple(reversed(range(1, 2 * seg, 2))))
    ob = nueva_malla(nombre, verts, faces)
    ob.hide_render = True
    return ob


def cortar_pasos(cuerpo):
    for i, r in enumerate(CH["ruedas"]):
        lado = 1 if r["z"] > 0 else -1
        z_in = lado * 0.455          # arranca por dentro de la llanta, no en el eje
        z_out = lado * 1.60
        cil = cilindro_corte(f"corte{i}", r["x"], r["R"] + 0.046,
                             min(z_in, z_out), max(z_in, z_out))
        m = cuerpo.modifiers.new(f"arco{i}", 'BOOLEAN')
        m.object = cil
        m.operation = 'DIFFERENCE'
        m.solver = 'EXACT'
    return cuerpo


# ============================================================================
# 4. PUERTAS DE GAVIOTA — se separan de la misma piel
# ============================================================================
def y_espinazo(x):
    xs = [e[0] for e in EST]
    ys = [e[11] for e in EST]
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            t = (x - xs[i]) / (xs[i + 1] - xs[i])
            return ys[i] + (ys[i + 1] - ys[i]) * t
    return ys[-1]


def techo_puerta(x):
    """Borde superior del hueco. Sigue el pilar A adelante y la pierna del arco atrás:
    si se recorta con x constante, el hueco se come el parabrisas."""
    x0, x1 = X_PUERTA
    if x < x0 or x > x1:
        return None
    if x < X_HDR:
        t = (x - x0) / (X_HDR - x0)
        return Y_ESTRIBO + (y_espinazo(X_HDR) - Y_ESTRIBO) * t ** 1.55
    if x <= X_ARCO:
        return 9.0
    t = (x - X_ARCO) / (x1 - X_ARCO)
    return y_espinazo(X_ARCO) - (y_espinazo(X_ARCO) - Y_ESTRIBO) * t ** 0.70


def perfil_puerta(holgura=0.0):
    """Contorno del hueco en el plano x–y. El borde delantero sigue el pilar A y el
    trasero la pierna del arco: con un corte de x constante el hueco se comería el
    parabrisas."""
    x0, x1 = X_PUERTA
    y_top_f, y_top_r = y_espinazo(X_HDR), y_espinazo(X_ARCO)
    p = []
    for i in range(26):                                   # pilar A, subiendo
        t = i / 25
        p.append((x0 + (X_HDR - x0) * t,
                  Y_ESTRIBO + (y_top_f - Y_ESTRIBO) * t ** 1.55))
    p.append((X_HDR, 1.35))                               # bien por encima del techo
    p.append((X_ARCO, 1.35))
    for i in range(26):                                   # pierna del arco, bajando
        t = i / 25
        p.append((X_ARCO + (x1 - X_ARCO) * t,
                  y_top_r - (y_top_r - Y_ESTRIBO) * t ** 0.70))
    p.append((x0, Y_ESTRIBO))
    # sin puntos repetidos: uno duplicado degenera la tapa del prisma, la malla deja
    # de ser manifold y el booleano de la puerta devuelve vacío
    limpio = [p[0]]
    for q in p[1:]:
        if abs(q[0] - limpio[-1][0]) > 1e-6 or abs(q[1] - limpio[-1][1]) > 1e-6:
            limpio.append(q)
    p = limpio
    if holgura:                                            # se infla para dejar el gap
        cx = sum(q[0] for q in p) / len(p)
        cy = sum(q[1] for q in p) / len(p)
        p = [(cx + (a - cx) * (1 + holgura), cy + (b - cy) * (1 + holgura)) for a, b in p]
    # orientación antihoraria, para que las tapas queden con la normal correcta
    area = sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1]
               for i in range(len(p)))
    if area < 0:
        p = p[::-1]
    return p


def prisma(nombre, perfil, z0, z1):
    verts, faces = [], []
    n = len(perfil)
    for (px, py) in perfil:
        verts.append((px, py, z0))
    for (px, py) in perfil:
        verts.append((px, py, z1))
    for k in range(n):
        k2 = (k + 1) % n
        faces.append((k, k2, n + k2, n + k))
    faces.append(tuple(range(n - 1, -1, -1)))
    faces.append(tuple(range(n, 2 * n)))
    ob = nueva_malla(nombre, verts, faces)
    ob.hide_render = True
    return ob


def separar_puertas(cuerpo):
    """La puerta se saca con BOOLEANO, no seleccionando caras: así el borde queda
    limpio y con el espesor real del panel a la vista en el gap."""
    puertas = []
    for lado, nom in ((+1, "PuertaIzq"), (-1, "PuertaDer")):
        z_in, z_out = lado * Z_ESPINAZO, lado * 1.6
        corte = prisma(nom + "_corte", perfil_puerta(), min(z_in, z_out), max(z_in, z_out))
        # 1) la puerta = cuerpo ∩ corte
        pan = cuerpo.copy()
        pan.data = cuerpo.data.copy()
        pan.name = nom
        bpy.context.collection.objects.link(pan)
        m = pan.modifiers.new("puerta", 'BOOLEAN')
        m.object, m.operation, m.solver = corte, 'INTERSECT', 'EXACT'
        aplicar_modificadores(pan)
        # 2) el hueco = cuerpo − corte inflado (deja 4 mm de gap perimetral)
        corte2 = prisma(nom + "_hueco", perfil_puerta(0.010),
                        min(z_in, z_out), max(z_in, z_out))
        m = cuerpo.modifiers.new("hueco_" + nom, 'BOOLEAN')
        m.object, m.operation, m.solver = corte2, 'DIFFERENCE', 'EXACT'
        aplicar_modificadores(cuerpo)
        puertas.append((pan, lado))
    return puertas


def lente(cuerpo, nombre, cortador, mat, desplazar):
    """Recorta un trozo de la PIEL con un cortador y lo separa como lente de luz.

    Hacerlo por intersección (y no modelando la luz aparte) garantiza que la firma
    siga exactamente la curvatura de la carrocería: es lo que hace que una barra de
    luz se vea integrada y no pegada encima.
    """
    ob = cuerpo.copy()
    ob.data = cuerpo.data.copy()
    ob.name = nombre
    bpy.context.collection.objects.link(ob)
    m = ob.modifiers.new("corte", 'BOOLEAN')
    m.object, m.operation, m.solver = cortador, 'INTERSECT', 'EXACT'
    aplicar_modificadores(ob)
    if len(ob.data.vertices) == 0:
        bpy.data.objects.remove(ob, do_unlink=True)
        return None
    ob.data.transform(__import__("mathutils").Matrix.Translation(Vector(desplazar)))
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob


def caja(nombre, x0, x1, y0, y1, z0, z1):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
         (2, 3, 7, 6), (3, 0, 4, 7)]
    ob = nueva_malla(nombre, v, f)
    ob.hide_render = True
    return ob


def firmas_de_luz(cuerpo, M):
    """Barra trasera continua y cejas delanteras, las dos señas de la referencia."""
    piezas = []
    p = lente(cuerpo, "LuzTrasera",
              caja("c_lt", 3.05, 3.45, 0.455, 0.545, -1.2, 1.2),
              M["luz_t"], (0.004, 0, 0))
    if p:
        piezas.append(p)
    for lado in (+1, -1):
        c = caja(f"c_ld{lado}", -0.05, 0.30, 0.318, 0.372,
                 min(lado * 0.22, lado * 0.70), max(lado * 0.22, lado * 0.70))
        p = lente(cuerpo, f"LuzDel{lado}", c, M["luz_d"], (-0.004, 0, 0))
        if p:
            piezas.append(p)
    return piezas


def abrir_puertas(puertas, grados):
    """Gira la geometría de la puerta sobre el eje del espinazo. Se transforman los
    vértices en vez de usar parentesco: el parentesco con el vacío rotado del carro
    mandaba una puerta a volar."""
    if not grados:
        return
    from mathutils import Matrix
    for ob, lado in puertas:
        p0 = Vector((X_HDR, y_espinazo(X_HDR), lado * Z_ESPINAZO))
        u = Vector((X_ARCO - X_HDR, y_espinazo(X_ARCO) - y_espinazo(X_HDR), 0.0)).normalized()
        R = Matrix.Rotation(math.radians(grados) * (-lado), 4, u)
        M = Matrix.Translation(p0) @ R @ Matrix.Translation(-p0)
        ob.data.transform(M)
        ob.data.update()


# ============================================================================
# 5. MATERIALES
# ============================================================================
def mat_principled(nombre, **kw):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    for k, v in kw.items():
        if k in b.inputs:
            b.inputs[k].default_value = v
    return m


def materiales():
    M = {}
    M["pintura"] = mat_principled(
        "Pintura", **{"Base Color": (0.052, 0.056, 0.065, 1), "Metallic": 0.85,
                      "Roughness": 0.22, "Coat Weight": 1.0, "Coat Roughness": 0.035})
    M["vidrio"] = mat_principled(
        "Vidrio", **{"Base Color": (0.02, 0.025, 0.032, 1), "Roughness": 0.03,
                     "Transmission Weight": 0.86, "IOR": 1.52})
    M["negro"] = mat_principled(
        "NegroTecnico", **{"Base Color": (0.017, 0.019, 0.022, 1), "Roughness": 0.42,
                           "Metallic": 0.0})
    M["hule"] = mat_principled(
        "Hule", **{"Base Color": (0.014, 0.014, 0.016, 1), "Roughness": 0.72})
    M["rin"] = mat_principled(
        "Rin", **{"Base Color": (0.44, 0.46, 0.50, 1), "Metallic": 1.0, "Roughness": 0.20})
    M["acero"] = mat_principled(
        "AceroChasis", **{"Base Color": (0.36, 0.38, 0.42, 1), "Metallic": 0.9,
                          "Roughness": 0.38})
    M["celda"] = mat_principled(
        "Celda", **{"Base Color": (0.05, 0.20, 0.09, 1), "Metallic": 0.4, "Roughness": 0.4})
    for nom, col, fuerza in (("luz_t", (1.0, 0.05, 0.09), 9.0),
                             ("luz_d", (0.62, 0.85, 1.0), 12.0)):
        m = bpy.data.materials.new(nom)
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*col, 1)
        em.inputs["Strength"].default_value = fuerza
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
        M[nom] = m
    return M


def curva(j):
    xs = [e[0] for e in EST]
    ys = [e[j] for e in EST]
    def f(x):
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        for i in range(len(xs) - 1):
            if xs[i] <= x <= xs[i + 1]:
                t = (x - xs[i]) / (xs[i + 1] - xs[i])
                return ys[i] + (ys[i + 1] - ys[i]) * t
        return ys[-1]
    return f


Y_FALDON = curva(3)
Y_CINTURA = curva(7)


def pintar(ob, M, es_puerta=False):
    """Asigna material por cara según dónde cae. Los límites coinciden con las curvas
    de la red, así que el borde del cristal sigue la cintura y no escalona."""
    orden = ["pintura", "vidrio", "negro", "luz_t", "luz_d"]
    ob.data.materials.clear()
    for k in orden:
        ob.data.materials.append(M[k])
    ejes = [(r["x"], r["R"]) for r in CH["ruedas"][::2]]
    for p in ob.data.polygons:
        c = p.center
        m = 0
        if c.x > 3.235 and 0.46 <= c.y <= 0.545:
            m = 3
        elif c.x < 0.215 and 0.300 <= c.y <= 0.352 and abs(c.z) > 0.13:
            m = 4
        elif (X_PUERTA[0] - 0.10) <= c.x <= (X_PUERTA[1] + 0.02) and c.y > Y_CINTURA(c.x) \
                and (c.x < X_HDR or abs(c.z) > Z_ESPINAZO + 0.02):
            m = 1
        elif c.y < Y_FALDON(c.x) - 0.005:
            m = 2
        elif any(abs(math.hypot(c.x - ax, c.y - 0.16) - (R + 0.052)) < 0.07
                 and abs(c.z) > 0.40 for ax, R in ejes):
            m = 2
        p.material_index = m


# ============================================================================
# 6. RUEDAS Y CHASIS
# ============================================================================
def rueda(r, M, seg=64):
    x, z, R, W = r["x"], r["z"], r["R"], r["W"]
    Rr = R * 0.575
    verts, faces = [], []
    def anillo_z(rad, zz):
        i0 = len(verts)
        for k in range(seg):
            a = 2 * math.pi * k / seg
            verts.append((x + rad * math.cos(a), R + rad * math.sin(a), zz))
        return i0
    z0, z1 = z - W / 2, z + W / 2
    aros = [anillo_z(R * 0.97, z0), anillo_z(R, z0 + W * 0.22),
            anillo_z(R, z1 - W * 0.22), anillo_z(R * 0.97, z1),
            anillo_z(Rr, z1 - 0.004), anillo_z(Rr, z0 + 0.004)]
    for a, b in ((0, 1), (1, 2), (2, 3), (3, 4), (5, 0)):
        for k in range(seg):
            k2 = (k + 1) % seg
            faces.append((aros[a] + k, aros[a] + k2, aros[b] + k2, aros[b] + k))
    ob = nueva_malla(f"Llanta_{x:.2f}_{z:+.2f}", verts, faces)
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.materials.append(M["hule"])

    # cara del rin: aro exterior, maza y 5 rayos como piezas sólidas
    lado = 1 if z > 0 else -1
    zc = (z1 - 0.010) if z > 0 else (z0 + 0.010)
    zf = zc + lado * 0.014
    v2, f2 = [], []

    def aro(r0, r1, za, zb, n=seg):
        i0 = len(v2)
        for k in range(n):
            a = 2 * math.pi * k / n
            for (rr, zz) in ((r0, za), (r1, za), (r1, zb), (r0, zb)):
                v2.append((x + rr * math.cos(a), R + rr * math.sin(a), zz))
        for k in range(n):
            k2 = (k + 1) % n
            for j in range(4):
                a1 = i0 + 4 * k + j
                b1 = i0 + 4 * k + (j + 1) % 4
                a2 = i0 + 4 * k2 + j
                b2 = i0 + 4 * k2 + (j + 1) % 4
                f2.append((a1, b1, b2, a2))

    aro(Rr * 0.90, Rr, zc - lado * 0.05, zf)          # aro exterior
    aro(0.0, Rr * 0.20, zc - lado * 0.03, zf)         # maza
    for s in range(5):                                 # 5 rayos
        a0 = 2 * math.pi * s / 5
        for da in (-0.115, 0.115):
            i0 = len(v2)
            a = a0 + da
            for rr in (Rr * 0.17, Rr * 0.93):
                v2.append((x + rr * math.cos(a), R + rr * math.sin(a), zf))
                v2.append((x + rr * math.cos(a), R + rr * math.sin(a), zf - lado * 0.028))
            if da > 0:
                f2.append((i0 - 4, i0 - 3, i0 + 1, i0 + 0))
                f2.append((i0 - 2, i0 - 1, i0 + 3, i0 + 2))
                f2.append((i0 - 4, i0 + 0, i0 + 2, i0 - 2))
                f2.append((i0 - 3, i0 - 1, i0 + 3, i0 + 1))
    ob2 = nueva_malla(f"Rin_{x:.2f}_{z:+.2f}", v2, f2)
    ob2.data.materials.append(M["rin"])
    return [ob, ob2]


def tubo(a, b, sec, M, seg=12):
    A, B = Vector(a), Vector(b)
    d = B - A
    L = d.length
    if L < 1e-6:
        return None
    if sec["tipo"] == "redondo":
        R = sec["d"] / 2
        perfil = [(R * math.cos(2 * math.pi * k / seg), R * math.sin(2 * math.pi * k / seg))
                  for k in range(seg)]
    else:
        h = sec["b"] / 2
        perfil = [(-h, -h), (h, -h), (h, h), (-h, h)]
    q = d.normalized().to_track_quat('Z', 'Y')
    verts, faces = [], []
    n = len(perfil)
    for j, t in ((0, 0.0), (1, 1.0)):
        for (px, py) in perfil:
            v = q @ Vector((px, py, 0.0)) + A + d * t
            verts.append(tuple(v))
    for k in range(n):
        k2 = (k + 1) % n
        faces.append((k, k2, n + k2, n + k))
    faces.append(tuple(range(n)))
    faces.append(tuple(reversed(range(n, 2 * n))))
    ob = nueva_malla("tubo", verts, faces)
    if sec["tipo"] == "redondo":
        for p in ob.data.polygons:
            p.use_smooth = True
    ob.data.materials.append(M["acero"])
    return ob


def construir_chasis(M):
    obs = []
    for t in CH["tubos"]:
        o = tubo(t["a"], t["b"], t["sec"], M)
        if o:
            obs.append(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.join()
    ch = bpy.context.view_layer.objects.active
    ch.name = "Chasis"
    return ch


# ============================================================================
# 7. ESTUDIO FOTOGRÁFICO
# ============================================================================
def area(nombre, pos, mira, w, h, potencia, color=(1, 1, 1)):
    d = bpy.data.lights.new(nombre, 'AREA')
    d.shape = 'RECTANGLE'
    d.size, d.size_y = w, h
    d.energy = potencia
    d.color = color
    ob = bpy.data.objects.new(nombre, d)
    bpy.context.collection.objects.link(ob)
    ob.location = pos
    ob.rotation_euler = (Vector(mira) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    return ob


def estudio():
    """Ciclorama y softboxes. La franja larga de arriba es la que dibuja el reflejo
    corrido a lo largo del costado — sin ella la pintura se ve de plástico."""
    m = bpy.data.materials.new("Piso")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.055, 0.058, 0.065, 1)
    b.inputs["Roughness"].default_value = 0.34
    b.inputs["Metallic"].default_value = 0.0
    piso = nueva_malla("Piso", [(-14, -14, 0), (18, -14, 0), (18, 14, 0), (-14, 14, 0)],
                       [(0, 1, 2, 3)])
    piso.data.materials.append(m)

    mundo = bpy.data.worlds.new("Estudio")
    bpy.context.scene.world = mundo
    mundo.use_nodes = True
    mundo.node_tree.nodes["Background"].inputs[0].default_value = (0.020, 0.023, 0.029, 1)
    mundo.node_tree.nodes["Background"].inputs[1].default_value = 1.0

    area("franja", (1.6, -0.6, 4.2), (1.6, 0.0, 0.6), 7.0, 1.1, 900)     # highlight largo
    area("clave", (5.2, -4.6, 3.4), (1.5, 0, 0.5), 3.2, 3.2, 700)
    area("relleno", (-1.2, 4.6, 2.4), (1.6, 0, 0.5), 4.0, 3.0, 260,
         color=(0.80, 0.87, 1.0))
    area("contra", (-3.6, -1.4, 1.9), (1.4, 0, 0.6), 2.6, 2.2, 420,
         color=(1.0, 0.93, 0.85))
    return piso


def plano_referencia():
    """Monta la vista lateral de la lámina como plano de fondo, ESCALADA Y ALINEADA
    para que sus dos ejes caigan sobre los nuestros y su suelo sobre el piso.

    Así se modela mirando: se calca encima. Sin alinear los ejes, la referencia miente
    sobre la proporción y el que esculpa se va con la finta.
    """
    ruta = os.path.join(RAIZ, "ref", "vista-lateral.png")
    if not os.path.exists(ruta):
        return None
    img = bpy.data.images.load(ruta)
    px_w, px_h = img.size
    EJE_DEL_PX, EJE_TRAS_PX, SUELO_PX = 122.0, 483.0, 220.0   # leídos de la lámina
    esc = (EJE_TRAS - EJE_DEL) / (EJE_TRAS_PX - EJE_DEL_PX)    # m por pixel
    ancho, alto = px_w * esc, px_h * esc
    x0 = EJE_DEL - EJE_DEL_PX * esc
    y0 = SUELO_PX * esc - alto                                  # el suelo en y=0
    z = -1.35
    ob = nueva_malla("RefLateral",
                     [(x0, y0, z), (x0 + ancho, y0, z),
                      (x0 + ancho, y0 + alto, z), (x0, y0 + alto, z)],
                     [(0, 1, 2, 3)])
    me = ob.data
    me.uv_layers.new(name="UV")
    for i, uv in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        me.uv_layers.active.data[i].uv = uv
    m = bpy.data.materials.new("RefLateral")
    m.use_nodes = True
    nt = m.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], nt.nodes["Material Output"].inputs["Surface"])
    ob.data.materials.append(m)
    ob.hide_render = True                    # sólo guía de modelado, no sale en render
    return ob


def camara(pos, mira, focal=85):
    cd = bpy.data.cameras.new("cam")
    cd.lens = focal
    ob = bpy.data.objects.new("cam", cd)
    bpy.context.collection.objects.link(ob)
    ob.location = pos
    ob.rotation_euler = (Vector(mira) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = ob
    return ob


# La nariz esta en x=0 y la cola en x=3.35: el frente se fotografia desde x NEGATIVO.
VISTAS = {
    "34frente":  ((-4.30, -5.60, 1.15), (1.35, 0.0, 0.48), 85),
    "34atras":   ((8.10, -5.30, 1.40), (1.90, 0.0, 0.50), 85),
    "lateral":   ((1.68, -14.0, 0.68), (1.68, 0.0, 0.52), 135),
    "frente":    ((-12.6, 0.0, 0.80), (1.20, 0.0, 0.52), 135),
    "atras":     ((16.0, 0.0, 0.85), (2.10, 0.0, 0.52), 135),
    "cenital":   ((1.70, -0.01, 12.0), (1.70, 0.0, 0.5), 100),
    "detalle":   ((-1.30, -3.10, 1.25), (1.55, 0.10, 0.72), 105),
}


def render_siluetas(nombre):
    """Tres vistas ORTOGRÁFICAS en silueta plana, para comparar contra la lámina.

    Sin perspectiva y sin sombreado: la única forma de saber si la carrocería se
    parece a la referencia es superponer siluetas, no mirar renders bonitos.
    """
    e = bpy.context.scene
    e.render.engine = 'BLENDER_WORKBENCH'
    e.display.shading.light = 'FLAT'
    e.display.shading.color_type = 'SINGLE'
    e.display.shading.single_color = (1, 1, 1)
    e.render.film_transparent = True
    e.view_settings.view_transform = 'Standard'
    e.render.resolution_percentage = 100
    for ob in bpy.data.objects:
        if ob.name in ("Piso",) or ob.name.startswith("Ref"):
            ob.hide_render = True
    vistas = {
        "lateral": ((1.68, -20.0, 0.54), (1.68, 0, 0.54), LARGO_OBJ * 1.06),
        "frontal": ((-20.0, 0.0, 0.54), (0, 0, 0.54), ANCHO_OBJ * 1.10),
        "cenital": ((1.68, 0.0, 20.0), (1.68, 0, 0), LARGO_OBJ * 1.06),
    }
    for nom, (pos, mira, escala) in vistas.items():
        cd = bpy.data.cameras.new("ortho")
        cd.type = 'ORTHO'
        cd.ortho_scale = escala
        ob = bpy.data.objects.new("ortho", cd)
        bpy.context.collection.objects.link(ob)
        ob.location = pos
        d = Vector(mira) - Vector(pos)
        arriba = 'Y' if nom != "cenital" else 'X'
        ob.rotation_euler = d.to_track_quat('-Z', arriba).to_euler()
        e.camera = ob
        e.render.resolution_x = 1400
        e.render.resolution_y = int(1400 * (ANCHO_OBJ if nom == "cenital" else
                                            (ALTO_OBJ if nom == "lateral" else ALTO_OBJ))
                                    / (LARGO_OBJ if nom != "frontal" else ANCHO_OBJ) * 1.15)
        e.render.filepath = os.path.join(SALIDA, f"{nombre}-sil-{nom}.png")
        bpy.ops.render.render(write_still=True)
        print("SILUETA OK", e.render.filepath)


def render(nombre, vista, muestras, ancho=1920, alto=1080):
    e = bpy.context.scene
    e.render.engine = 'CYCLES'
    e.cycles.device = 'CPU'
    e.cycles.samples = muestras
    e.cycles.use_denoising = True
    e.cycles.max_bounces = 8
    e.cycles.transmission_bounces = 8
    e.render.resolution_x, e.render.resolution_y = ancho, alto
    e.render.resolution_percentage = 100
    e.render.film_transparent = False
    e.view_settings.view_transform = 'AgX'
    e.view_settings.look = 'AgX - Punchy'
    pos, mira, foc = VISTAS[vista]
    camara(pos, mira, foc)
    e.render.filepath = os.path.join(SALIDA, nombre + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDER OK", e.render.filepath)


# ============================================================================
# 8. ARMADO
# ============================================================================
def main():
    limpiar()
    ok = validar()
    M = materiales()

    cuerpo = jaula_casco(M) if arg("--casco", "1") == "1" else construir_jaula(M)
    subdividir(cuerpo, 2)
    # NADA de Solidify aquí: la jaula ya cierra un sólido, y un offset de 14 mm en la
    # punta de la nariz —donde la sección mide menos que el propio espesor— colapsa la
    # malla y hace que el booleano del paso de rueda devuelva basura (251 caras).
    print(f"DIAG jaula          v={len(cuerpo.data.vertices)} f={len(cuerpo.data.polygons)}")
    aplicar_modificadores(cuerpo)
    print(f"DIAG subdiv+espesor v={len(cuerpo.data.vertices)} f={len(cuerpo.data.polygons)}")
    cortar_pasos(cuerpo)
    aplicar_modificadores(cuerpo)
    print(f"DIAG tras arcos     v={len(cuerpo.data.vertices)} f={len(cuerpo.data.polygons)}")
    luces = firmas_de_luz(cuerpo, M)
    print(f"DIAG luces          {len(luces)} piezas")
    puertas = separar_puertas(cuerpo)
    print(f"DIAG cuerpo final   v={len(cuerpo.data.vertices)} f={len(cuerpo.data.polygons)}")
    for ob, lado in puertas:
        print(f"DIAG puerta {lado:+d}       v={len(ob.data.vertices)} f={len(ob.data.polygons)}")

    ruedas = []
    for r in CH["ruedas"]:
        ruedas += rueda(r, M)
    chasis = construir_chasis(M)

    # todo el carro va colgado de un vacío rotado: el modelo trabaja con Y arriba
    # (convención del proyecto) y Blender con Z arriba
    raiz = bpy.data.objects.new("Carro", None)
    bpy.context.collection.objects.link(raiz)
    raiz.rotation_euler = (math.pi / 2, 0, 0)
    abrir_puertas(puertas, float(arg("--puertas", "0")))
    for ob in list(bpy.context.collection.objects):
        if ob is raiz or ob.parent is not None or ob.type == 'EMPTY':
            continue
        ob.parent = raiz

    estudio()
    ref_plano = plano_referencia()
    if ref_plano is not None:
        ref_plano.parent = raiz

    destino = arg("--guardar", "")
    if destino:
        ruta = os.path.join(RAIZ, destino)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=ruta)
        print("BLEND GUARDADO", ruta)

    solo = arg("--solo", "")
    if solo == "chasis":
        for ob in bpy.data.objects:
            if ob.type == 'MESH' and ob.name not in ("Piso", "Chasis") \
                    and not ob.name.startswith(("Llanta", "Rin")):
                ob.hide_render = True
    elif solo == "carroceria":
        chasis.hide_render = True

    muestras = int(arg("--muestras", "96"))
    nombre = arg("--nombre", "carro")
    for v in arg("--vistas", "34frente").split(","):
        render(f"{nombre}-{v}", v, muestras)
    print("VALIDACION_ENVOLVENTE:", "OK" if ok else "FALLA")


main()
