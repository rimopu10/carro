# -*- coding: utf-8 -*-
"""
Convierte la malla de la IA en una SUPERFICIE PARAMÉTRICA que se puede editar.

Por qué hace falta: lo que entrega el reconstructor son 2 millones de triángulos sin
topología, sin simetría y sin espesor. Se puede mirar, no se puede fabricar ni
modificar. Aquí se le extraen secciones transversales, se limpian, se simetrizan y se
reconstruye como REJILLA DE CUADRÁNGULOS — que es lo que permite después sacar
paneles, darle espesor, trocearla para imprimir y derivar el chasis de ella.

Método de la sección: barrido radial. Para cada estación se toman los vértices de una
rebanada y, por sector angular, se queda el radio máximo desde un centro interior. Eso
da un contorno cerrado y ordenado. Limitación honesta: un barrido radial no captura
concavidades profundas (la toma de aire lateral se suaviza); esos detalles se vuelven
a cortar después sobre la superficie limpia.

    blender --background --python render/extraer_secciones.py -- --glb cad/gem-mv3.glb
"""
import json
import math
import os
import sys

import bpy
import bmesh
import mathutils
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(n, d):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAD = os.path.join(RAIZ, "cad")
CH = json.load(open(os.path.join(CAD, "chasis.json"), encoding="utf-8"))

EJE_DEL = CH["ruedas"][0]["x"]
EJE_TRAS = CH["ruedas"][2]["x"]
LARGO = float(arg("--largo", "3.35"))
ANCHO = float(arg("--ancho", "1.82"))
N_EST = int(arg("--estaciones", "120"))      # rebanadas a lo largo
N_ANG = int(arg("--angulos", "128"))         # puntos por sección (par: se simetriza)
# ejes de la referencia como fracción del largo (medido por calculos/silueta_ref.py)
EJE_DEL_REF, EJE_TRAS_REF = 0.202, 0.832


def caja(o):
    vs = [v.co for v in o.data.vertices]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return mn, mx, mx - mn


def cargar_y_limpiar(glb):
    bpy.ops.import_scene.gltf(filepath=glb)
    ms = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in ms:
        o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    if len(ms) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    mn, mx, d = caja(ob)
    if d.y > d.x:
        ob.data.transform(mathutils.Matrix.Rotation(math.radians(-90), 4, 'Z'))
        ob.data.update()
        mn, mx, d = caja(ob)
    if d.z > d.y:
        ob.data.transform(mathutils.Matrix.Rotation(math.radians(90), 4, 'X'))
        ob.data.update()
        mn, mx, d = caja(ob)

    # pedestal fusionado
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                           plane_co=(0, 0, mn.z + d.z * 0.030), plane_no=(0, 0, 1),
                           clear_inner=True)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()

    # morro a x mínimo
    vs = [v.co for v in ob.data.vertices]
    x0, x1 = min(v.x for v in vs), max(v.x for v in vs)
    L = x1 - x0
    ini = [v.z for v in vs if v.x < x0 + 0.10 * L]
    fin = [v.z for v in vs if v.x > x1 - 0.10 * L]
    if sum(ini) / len(ini) > sum(fin) / len(fin):
        ob.data.transform(mathutils.Matrix.Rotation(math.radians(180), 4, 'Z'))
        ob.data.update()
    print(f"LIMPIA         {len(ob.data.polygons)} caras")
    return ob


def a_convencion_proyecto(ob):
    """Largo en X, ALTURA en Y y lateral en Z, que es lo que usa todo el proyecto
    (chasis, ruedas, cortadores). Se gira, no se intercambian ejes: intercambiarlos
    tiene determinante -1 y espejaría la pieza."""
    ob.data.transform(mathutils.Matrix.Rotation(math.radians(-90), 4, 'X'))
    ob.data.update()


def escalar_al_paquete(ob):
    """Ancla los DOS EJES: entre ejes 1:1 y sólo se estiran los voladizos. La batalla
    no se toca porque de ella cuelga toda la suspensión ya validada."""
    import numpy as np
    mn, mx, d = caja(ob)
    L = d.x
    x_ref = [mn.x, mn.x + EJE_DEL_REF * L, mn.x + EJE_TRAS_REF * L, mx.x]
    x_nos = [0.0, EJE_DEL, EJE_TRAS, LARGO]
    s = ANCHO / d.z
    for v in ob.data.vertices:
        v.co.x = float(np.interp(v.co.x, x_ref, x_nos))
        v.co.y = (v.co.y - mn.y) * s
        v.co.z = (v.co.z - (mn.z + mx.z) / 2) * s
    ob.data.update()
    mn, mx, d = caja(ob)
    print(f"AL PAQUETE     largo {d.x:.3f}  ancho {d.z:.3f}  alto {d.y:.3f} m")
    return d


# ============================================================================
# EXTRACCIÓN DE SECCIONES
# ============================================================================
def extraer(ob, alto):
    """Contorno de cada estación por RAYOS DESDE FUERA.

    Quedarse con el radio máximo de los vértices de una rebanada no sirve: la sección
    de un carro no es estrellada respecto a su centro —el cristal cae hacia dentro
    sobre el hombro— y el máximo se traga la caída, dejando un bulto liso. Lanzando
    rayos desde fuera hacia el centro y tomando el PRIMER impacto se obtiene la piel
    exterior real, con sus rebajes.
    """
    import numpy as np
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    arbol = BVHTree.FromBMesh(bm)

    xs = np.linspace(0.006, LARGO - 0.006, N_EST)
    med = N_ANG // 2
    secciones = np.zeros((N_EST, med))
    centros = np.zeros(N_EST)
    validas = np.zeros(N_EST, dtype=bool)
    R = max(ANCHO, alto) * 1.4
    vs = np.array([[v.co.x, v.co.y, v.co.z] for v in ob.data.vertices])
    paso = LARGO / N_EST

    for i, x in enumerate(xs):
        sel = vs[np.abs(vs[:, 0] - x) < paso * 0.9]
        if len(sel) < 20:
            continue
        cy = 0.5 * (sel[:, 1].min() + sel[:, 1].max())
        centros[i] = cy
        centro = Vector((float(x), float(cy), 0.0))
        acierto = 0
        for k in range(med):
            a = -math.pi / 2 + math.pi * k / (med - 1)
            # se promedian los dos lados: el carro es simétrico y promediar cancela
            # el ruido de la reconstrucción
            radios = []
            for signo in (+1, -1):
                dirn = Vector((0.0, math.sin(a), signo * math.cos(a)))
                origen = centro + dirn * R
                golpe = arbol.ray_cast(origen, -dirn, R * 2.0)
                if golpe[0] is not None:
                    radios.append((golpe[0] - centro).length)
            if radios:
                secciones[i, k] = sum(radios) / len(radios)
                acierto += 1
        if acierto < med * 0.5:
            continue
        vac = secciones[i] <= 0
        if vac.any():
            secciones[i, vac] = np.interp(np.flatnonzero(vac), np.flatnonzero(~vac),
                                          secciones[i, ~vac])
        validas[i] = True
    bm.free()

    # rellenar estaciones inválidas (morro y cola muy finos)
    if not validas.all():
        for k in range(med):
            secciones[:, k] = np.interp(np.arange(N_EST), np.flatnonzero(validas),
                                        secciones[validas, k])
        centros = np.interp(np.arange(N_EST), np.flatnonzero(validas), centros[validas])

    # suavizado: circunferencial primero, longitudinal después
    for _ in range(1):
        secciones = (np.roll(secciones, 1, axis=1) + 2 * secciones
                     + np.roll(secciones, -1, axis=1)) / 4
    for _ in range(1):
        secciones[1:-1] = (secciones[:-2] + 2 * secciones[1:-1] + secciones[2:]) / 4
        centros[1:-1] = (centros[:-2] + 2 * centros[1:-1] + centros[2:]) / 4
    print(f"SECCIONES      {int(validas.sum())} de {N_EST} medidas directamente")
    return xs, centros, secciones


def construir(xs, centros, secciones, alto):
    """Rejilla de cuadrángulos: N_EST anillos x N_ANG puntos. Topología limpia."""
    import numpy as np
    med = secciones.shape[1]
    verts, anillos = [], []
    for i, x in enumerate(xs):
        fila = []
        # lado +z: de abajo (ang=-90) a arriba (ang=+90)
        for k in range(med):
            a = -math.pi / 2 + math.pi * k / (med - 1)
            r = secciones[i, k]
            fila.append(len(verts))
            verts.append((float(x), float(centros[i] + r * math.sin(a)),
                          float(r * math.cos(a))))
        # lado -z: el espejo, sin repetir los dos polos
        for k in range(med - 2, 0, -1):
            a = -math.pi / 2 + math.pi * k / (med - 1)
            r = secciones[i, k]
            fila.append(len(verts))
            verts.append((float(x), float(centros[i] + r * math.sin(a)),
                          float(-r * math.cos(a))))
        anillos.append(fila)

    faces = []
    n = len(anillos[0])
    for i in range(len(anillos) - 1):
        A, B = anillos[i], anillos[i + 1]
        for k in range(n):
            k2 = (k + 1) % n
            faces.append((A[k], A[k2], B[k2], B[k]))
    faces.append(tuple(reversed(anillos[0])))
    faces.append(tuple(anillos[-1]))

    me = bpy.data.meshes.new("SuperficieParam")
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("SuperficieParam", me)
    bpy.context.collection.objects.link(ob)
    print(f"SUPERFICIE     {len(me.vertices)} vertices  {len(me.polygons)} cuadrangulos")
    return ob


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    glb = os.path.join(RAIZ, arg("--glb", "cad/gem-mv3.glb"))
    ob = cargar_y_limpiar(glb)
    a_convencion_proyecto(ob)
    d = escalar_al_paquete(ob)
    xs, centros, secciones = extraer(ob, d.y)

    datos = {
        "x": [round(float(v), 5) for v in xs],
        "centro_y": [round(float(v), 5) for v in centros],
        "radios": [[round(float(v), 5) for v in fila] for fila in secciones],
        "n_angulos": N_ANG,
        "cotas": {"largo": LARGO, "ancho": ANCHO, "alto": round(float(d.y), 4),
                  "eje_del": EJE_DEL, "eje_tras": EJE_TRAS},
    }
    dest = os.path.join(CAD, "superficie-param.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(datos, f, separators=(",", ":"))
    print("JSON           " + dest)

    bpy.data.objects.remove(ob, do_unlink=True)
    nuevo = construir(xs, centros, secciones, d.y)
    bpy.ops.object.select_all(action='DESELECT')
    nuevo.select_set(True)
    bpy.context.view_layer.objects.active = nuevo
    salida = os.path.join(CAD, "superficie-param.glb")
    bpy.ops.export_scene.gltf(filepath=salida, use_selection=True,
                              export_format='GLB')
    print("GLB            " + salida)


main()

