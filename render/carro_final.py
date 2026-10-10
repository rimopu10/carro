# -*- coding: utf-8 -*-
"""
El carro completo: carrocería de la IA + tu chasis + tus ruedas + gaviotas + luces.

Ningún modelo generativo entrega una llanta con rin, un faro con lente o una línea de
partición de puerta a calidad usable. Eso se ENSAMBLA, que es como se arma un modelo
de carro de verdad: la IA aporta el cascarón, y encima se le montan las piezas.

Cadena:
  1. Se limpia la malla de la IA (pedestal, cartel plano, orientación).
  2. Se REORIENTA a tu paquete anclando los DOS EJES: entre ejes va 1:1 y sólo se
     estiran los voladizos. La batalla no se toca porque de ella cuelga la suspensión.
  3. Se recortan los pasos de rueda en TUS posiciones de eje y se meten tus ruedas.
  4. Se cortan las puertas de gaviota sobre el espinazo.
  5. Se sacan las lentes de luz de la propia piel, para que sigan su curvatura.
  6. Se valida contra la envolvente medida del chasis: si un tubo asoma, avisa.

    blender --background --python render/carro_final.py -- --muestras 64
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
SALIDA = os.path.join(RAIZ, "render", "salida")
os.makedirs(SALIDA, exist_ok=True)
CH = json.load(open(os.path.join(RAIZ, "cad", "chasis.json"), encoding="utf-8"))

EJE_DEL = CH["ruedas"][0]["x"]
EJE_TRAS = CH["ruedas"][2]["x"]
LARGO_OBJ = float(arg("--largo", "3.35"))
ANCHO_OBJ = float(arg("--ancho", "1.82"))
Z_ESPINAZO = CH["duros"]["z_espinazo"]
X_HDR, Y_HDR = CH["duros"]["cabecera"]
X_ARCO, Y_ARCO = CH["duros"]["arco"]
X_PUERTA = (1.055, 2.120)
Y_ESTRIBO = 0.430

# Posición de los ejes en la referencia, medida por calculos/silueta_ref.py y
# expresada como fracción del largo. Es lo que permite anclar la reorientación.
EJE_DEL_REF, EJE_TRAS_REF = 0.202, 0.832


# ============================================================================
# utilidades de malla
# ============================================================================
def nueva_malla(nombre, verts, faces):
    me = bpy.data.meshes.new(nombre)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.collection.objects.link(ob)
    return ob


def caja(o):
    vs = [v.co for v in o.data.vertices]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return mn, mx, mx - mn


def aplicar(ob):
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def booleano(ob, cortador, operacion):
    m = ob.modifiers.new("bool", 'BOOLEAN')
    m.object, m.operation, m.solver = cortador, operacion, 'EXACT'
    aplicar(ob)


# ============================================================================
# 1. limpieza de la malla generada
# ============================================================================
def cargar_ia(glb):
    bpy.ops.import_scene.gltf(filepath=glb)
    mallas = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in mallas:
        o.select_set(True)
    bpy.context.view_layer.objects.active = mallas[0]
    if len(mallas) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = "Carroceria"
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

    # pedestal: el generador funde una placa de apoyo al cuerpo
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                           plane_co=(0, 0, mn.z + d.z * 0.030), plane_no=(0, 0, 1),
                           clear_inner=True)
    r = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary])
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()

    recortar_cartel(ob)
    orientar_morro(ob)
    return ob


def recortar_cartel(o):
    """Quita el panel plano que el generador deja parado contra un extremo."""
    import numpy as np
    vs = np.array([[v.co.x, v.co.y, v.co.z] for v in o.data.vertices])
    n = 160
    xs = np.linspace(vs[:, 0].min(), vs[:, 0].max(), n)
    alto = np.zeros(n - 1)
    for i in range(n - 1):
        sel = vs[(vs[:, 0] >= xs[i]) & (vs[:, 0] < xs[i + 1])]
        alto[i] = sel[:, 2].max() if len(sel) > 3 else 0.0
    H, total = alto.max(), vs[:, 0].max() - vs[:, 0].min()
    d = np.diff(alto)
    umbral, borde = 0.12 * H, int(n * 0.22)
    x_ini, x_fin = vs[:, 0].min(), vs[:, 0].max()
    caidas = [i for i in range(borde) if d[i] < -umbral]
    if caidas:
        x_ini = xs[max(caidas) + 1]
    subidas = [i for i in range(n - 1 - borde, n - 2) if d[i] > umbral]
    if subidas:
        x_fin = xs[min(subidas)]
    if (x_fin - x_ini) < 0.60 * total:
        print("CARTEL         descartado (recorte absurdo)")
        return
    if (x_ini - vs[:, 0].min()) < 0.004 * total and (vs[:, 0].max() - x_fin) < 0.004 * total:
        print("CARTEL         ninguno")
        return
    print(f"CARTEL         recortado a x=[{x_ini:.3f}, {x_fin:.3f}]")
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for co, no in (((x_ini, 0, 0), (-1, 0, 0)), ((x_fin, 0, 0), (1, 0, 0))):
        bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                               plane_co=co, plane_no=no, clear_outer=True)
    r = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary])
    tapas = [f for f in r.get("faces", []) if f.is_valid]
    if tapas:
        pk = bmesh.ops.poke(bm, faces=tapas)
        ar = {e for f in pk["faces"] if f.is_valid for e in f.edges}
        bmesh.ops.subdivide_edges(bm, edges=list(ar), cuts=10, use_grid_fill=True)
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()


def orientar_morro(o):
    """Deja el morro en x mínimo. El extremo del morro es más bajo que el de la cola."""
    vs = [v.co for v in o.data.vertices]
    x0, x1 = min(v.x for v in vs), max(v.x for v in vs)
    L = x1 - x0
    ini = [v.z for v in vs if v.x < x0 + 0.10 * L]
    fin = [v.z for v in vs if v.x > x1 - 0.10 * L]
    if sum(ini) / len(ini) > sum(fin) / len(fin):
        o.data.transform(mathutils.Matrix.Rotation(math.radians(180), 4, 'Z'))
        o.data.update()
        print("MORRO          estaba al revés, se giró 180°")
    else:
        print("MORRO          ya estaba en x mínimo")


# ============================================================================
# 2. REORIENTACIÓN al paquete: se anclan los dos ejes
# ============================================================================
def reorientar(o):
    """Lleva la carrocería a tus cotas SIN mover la batalla.

    Escalar todo por igual desplazaría los ejes y la suspensión dejaría de coincidir.
    En su lugar se hace un mapeo lineal por tramos en x con cuatro anclas — morro,
    eje delantero, eje trasero y cola — así entre ejes va 1:1 y sólo se comprimen o
    estiran los voladizos. Es lo que hace un diseñador al adaptar una proporción a
    otro chasis.
    """
    # CONVENCIÓN DE EJES. La malla llega con largo en X, ancho en Y y alto en Z. Todo
    # el proyecto (chasis, ruedas, cortadores) usa Y como ALTURA y Z como lateral.
    # Sin esta rotación los cilindros del paso de rueda cortan de plano y los prismas
    # de puerta quedan acostados. Se gira -90° en X (no se intercambian ejes: eso
    # espejaría la pieza).
    o.data.transform(mathutils.Matrix.Rotation(math.radians(-90), 4, 'X'))
    o.data.update()

    mn, mx, d = caja(o)
    L = d.x
    x_ref = [mn.x, mn.x + EJE_DEL_REF * L, mn.x + EJE_TRAS_REF * L, mx.x]
    x_nos = [0.0, EJE_DEL, EJE_TRAS, LARGO_OBJ]
    s = ANCHO_OBJ / d.z                      # un solo factor: no se deforma la sección

    import numpy as np
    for v in o.data.vertices:
        v.co.x = float(np.interp(v.co.x, x_ref, x_nos))
        v.co.y = (v.co.y - mn.y) * s
        v.co.z = (v.co.z - (mn.z + mx.z) / 2) * s
    o.data.update()
    if arg("--simetria", "1") == "1":
        simetrizar(o)
    if arg("--techo", "1") == "1":
        levantar_techo(o)
    mn, mx, d = caja(o)
    print(f"REORIENTADA    largo {d.x:.3f}  ancho {d.z:.3f}  alto {d.y:.3f} m   "
          f"(batalla anclada en {EJE_DEL:.2f}–{EJE_TRAS:.2f})")
    return d


def levantar_techo(o):
    """Sube el techo lo justo para que el arco y el pilar A queden dentro.

    La referencia es un carro 10 cm más bajo que el nuestro: su perfil de techo pasa
    por debajo de nuestra célula de seguridad. En vez de deformar la sección se aplica
    un factor vertical por estación —el piso queda clavado en 0 y todo sube en
    proporción— y se suaviza para que no aparezca un escalón.
    """
    import numpy as np
    vs = np.array([[v.co.x, v.co.y, v.co.z] for v in o.data.vertices])
    ex = [s["x"] for s in CH["envolvente"]]
    ehi = [s["y_hi"] for s in CH["envolvente"]]
    n = 90
    xs = np.linspace(vs[:, 0].min(), vs[:, 0].max(), n)
    factor = np.ones(n)
    for i, x in enumerate(xs):
        if x < ex[0] or x > ex[-1]:
            continue
        sel = vs[np.abs(vs[:, 0] - x) < 0.05]
        if len(sel) < 8:
            continue
        techo = sel[:, 1].max()
        necesario = float(np.interp(x, ex, ehi)) + 0.022
        if techo < necesario and techo > 1e-6:
            factor[i] = necesario / techo
    for _ in range(6):                       # suavizado: sin esto queda un escalón
        factor[1:-1] = 0.25 * factor[:-2] + 0.5 * factor[1:-1] + 0.25 * factor[2:]
    subida = factor.max()
    if subida <= 1.001:
        print("TECHO          no hizo falta levantarlo")
        return
    for v in o.data.vertices:
        v.co.y *= float(np.interp(v.co.x, xs, factor))
    o.data.update()
    print(f"TECHO          levantado hasta {(subida - 1) * 100:.1f}% en la cabina")


def simetrizar(o):
    """Refleja la mitad izquierda sobre la derecha.

    La reconstrucción no sale simétrica —las dos vistas de costado que se le dan no
    son idénticas pixel a pixel— y esa asimetría rompía el booleano de la puerta
    derecha: la malla quedaba no-manifold de un lado. Un carro es simétrico, así que
    imponerlo es correcto y además arregla los cortes."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                           plane_co=(0, 0, 0), plane_no=(0, 0, 1), clear_outer=True)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    dup = bmesh.ops.duplicate(bm, geom=geom)
    vs = [g for g in dup["geom"] if isinstance(g, bmesh.types.BMVert)]
    fs = [g for g in dup["geom"] if isinstance(g, bmesh.types.BMFace)]
    bmesh.ops.scale(bm, vec=(1, 1, -1), verts=vs)
    bmesh.ops.reverse_faces(bm, faces=fs)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0006)
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    print(f"SIMETRIZADA    {len(o.data.polygons)} caras")


def validar_envolvente(o):
    """¿La carrocería contiene el chasis? Se mide contra la envolvente real."""
    import numpy as np
    vs = np.array([[v.co.x, v.co.y, v.co.z] for v in o.data.vertices])
    faltas = []
    for s in CH["envolvente"]:
        x = s["x"]
        sel = vs[np.abs(vs[:, 0] - x) < 0.045]
        if len(sel) < 8:
            continue
        holg_z = np.abs(sel[:, 2]).max() - s["z"]      # ancho: lateral = indice 2
        holg_y = s["y_lo"] - sel[:, 1].min()            # piso:  altura = indice 1
        holg_t = sel[:, 1].max() - s["y_hi"]
        peor = min(holg_z, holg_y, holg_t)
        if peor < 0.008:
            faltas.append((x, holg_z * 1000, holg_y * 1000, holg_t * 1000))
    print("=" * 68)
    if not faltas:
        print("ENVOLVENTE     OK — ningún tubo asoma de la carrocería")
    else:
        print(f"ENVOLVENTE     {len(faltas)} estaciones con menos de 8 mm:")
        for x, a, b, c in faltas[:10]:
            print(f"   x={x:5.2f}   ancho {a:+7.1f}   piso {b:+7.1f}   techo {c:+7.1f} mm")
    print("=" * 68)
    return not faltas


# ============================================================================
# 3. RUEDAS: se recorta el bulto que trae la IA y se meten las tuyas
# ============================================================================
def cilindro(nombre, x, R, z0, z1, seg=80):
    verts, faces = [], []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        verts.append((x + R * math.cos(a), 0.16 + R * math.sin(a), z0))
        verts.append((x + R * math.cos(a), 0.16 + R * math.sin(a), z1))
    for k in range(seg):
        a, b = 2 * k, 2 * ((k + 1) % seg)
        faces.append((a, b, b + 1, a + 1))
    faces.append(tuple(range(0, 2 * seg, 2)))
    faces.append(tuple(reversed(range(1, 2 * seg, 2))))
    ob = nueva_malla(nombre, verts, faces)
    ob.hide_render = True
    return ob


def rueda(r, M, seg=72):
    """Llanta con hombros redondeados y rin de 5 rayos. La IA entrega discos lisos."""
    x, z, R, W = r["x"], r["z"], r["R"], r["W"]
    Rr = R * 0.60
    lado = 1 if z > 0 else -1
    z0, z1 = z - W / 2, z + W / 2
    verts, faces = [], []

    def aro(rad, zz):
        i0 = len(verts)
        for k in range(seg):
            a = 2 * math.pi * k / seg
            verts.append((x + rad * math.cos(a), R + rad * math.sin(a), zz))
        return i0

    aros = [aro(R * 0.955, z0), aro(R, z0 + W * 0.20), aro(R, z1 - W * 0.20),
            aro(R * 0.955, z1), aro(Rr, z1 - 0.006), aro(Rr, z0 + 0.006)]
    for a, b in ((0, 1), (1, 2), (2, 3), (3, 4), (5, 0)):
        for k in range(seg):
            k2 = (k + 1) % seg
            faces.append((aros[a] + k, aros[a] + k2, aros[b] + k2, aros[b] + k))
    llanta = nueva_malla(f"Llanta{x:.2f}{z:+.2f}", verts, faces)
    for p in llanta.data.polygons:
        p.use_smooth = True
    llanta.data.materials.append(M["hule"])

    v2, f2 = [], []
    zf = (z1 - 0.008) if lado > 0 else (z0 + 0.008)
    zb = zf - lado * 0.030

    def anillo3d(r0, r1, za, zb_, n=seg):
        i0 = len(v2)
        for k in range(n):
            a = 2 * math.pi * k / n
            for (rr, zz) in ((r0, za), (r1, za), (r1, zb_), (r0, zb_)):
                v2.append((x + rr * math.cos(a), R + rr * math.sin(a), zz))
        for k in range(n):
            k2 = (k + 1) % n
            for j in range(4):
                f2.append((i0 + 4 * k + j, i0 + 4 * k + (j + 1) % 4,
                           i0 + 4 * k2 + (j + 1) % 4, i0 + 4 * k2 + j))

    anillo3d(Rr * 0.88, Rr, zb, zf)                     # aro exterior
    anillo3d(0.0, Rr * 0.22, zb - lado * 0.02, zf)      # maza
    for s in range(5):                                   # rayos
        a0 = 2 * math.pi * s / 5
        for da in (-0.13, 0.13):
            i0 = len(v2)
            a = a0 + da
            for rr in (Rr * 0.19, Rr * 0.90):
                v2.append((x + rr * math.cos(a), R + rr * math.sin(a), zf))
                v2.append((x + rr * math.cos(a), R + rr * math.sin(a), zb))
            if da > 0:
                f2 += [(i0 - 4, i0 - 3, i0 + 1, i0 + 0), (i0 - 2, i0 - 1, i0 + 3, i0 + 2),
                       (i0 - 4, i0 + 0, i0 + 2, i0 - 2), (i0 - 3, i0 - 1, i0 + 3, i0 + 1)]
    rin = nueva_malla(f"Rin{x:.2f}{z:+.2f}", v2, f2)
    rin.data.materials.append(M["rin"])
    return [llanta, rin]


# ============================================================================
# 4. PUERTAS DE GAVIOTA
# ============================================================================
def perfil_puerta(holgura=0.0):
    x0, x1 = X_PUERTA
    yf, yr = 1.02, 1.03
    p = [(x0 + (X_HDR - x0) * (i / 25),
          Y_ESTRIBO + (yf - Y_ESTRIBO) * (i / 25) ** 1.55) for i in range(26)]
    p += [(X_HDR, 1.45), (X_ARCO, 1.45)]
    p += [(X_ARCO + (x1 - X_ARCO) * (i / 25),
           yr - (yr - Y_ESTRIBO) * (i / 25) ** 0.70) for i in range(26)]
    p.append((x0, Y_ESTRIBO))
    limpio = [p[0]]
    for q in p[1:]:
        if abs(q[0] - limpio[-1][0]) > 1e-6 or abs(q[1] - limpio[-1][1]) > 1e-6:
            limpio.append(q)
    p = limpio
    if holgura:
        cx = sum(q[0] for q in p) / len(p)
        cy = sum(q[1] for q in p) / len(p)
        p = [(cx + (a - cx) * (1 + holgura), cy + (b - cy) * (1 + holgura)) for a, b in p]
    area = sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1]
               for i in range(len(p)))
    return p[::-1] if area < 0 else p


def prisma(nombre, perfil, z0, z1):
    n = len(perfil)
    verts = [(a, b, z0) for a, b in perfil] + [(a, b, z1) for a, b in perfil]
    faces = [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    faces.append(tuple(range(n - 1, -1, -1)))
    faces.append(tuple(range(n, 2 * n)))
    ob = nueva_malla(nombre, verts, faces)
    ob.hide_render = True
    return ob


def separar_puertas(cuerpo, M):
    """Primero se EXTRAEN los dos paneles del cuerpo íntegro, y sólo después se le
    hacen los huecos. Encadenar extracción y corte lado por lado deja la malla
    no-manifold tras el primer corte y el segundo booleano devuelve vacío — así se
    perdían la puerta derecha y una ceja."""
    puertas, huecos = [], []
    for lado, nom in ((+1, "PuertaIzq"), (-1, "PuertaDer")):
        z_in, z_out = lado * Z_ESPINAZO, lado * 1.8
        z0, z1 = min(z_in, z_out), max(z_in, z_out)
        pan = cuerpo.copy()
        pan.data = cuerpo.data.copy()
        pan.name = nom
        bpy.context.collection.objects.link(pan)
        booleano(pan, prisma(nom + "_c", perfil_puerta(), z0, z1), 'INTERSECT')
        if len(pan.data.vertices) == 0:
            bpy.data.objects.remove(pan, do_unlink=True)
            print(f"PUERTA {lado:+d}       FALLO (booleano vacio)")
            continue
        puertas.append((pan, lado))
        huecos.append(prisma(nom + "_h", perfil_puerta(0.009), z0, z1))
        print(f"PUERTA {lado:+d}       {len(pan.data.polygons)} caras")
    for h in huecos:
        booleano(cuerpo, h, 'DIFFERENCE')
    return puertas


def abrir_puertas(puertas, grados):
    if not grados:
        return
    for ob, lado in puertas:
        p0 = Vector((X_HDR, 1.02, lado * Z_ESPINAZO))
        u = Vector((X_ARCO - X_HDR, 0.01, 0.0)).normalized()
        R = mathutils.Matrix.Rotation(math.radians(grados) * (-lado), 4, u)
        ob.data.transform(mathutils.Matrix.Translation(p0) @ R @
                          mathutils.Matrix.Translation(-p0))
        ob.data.update()


# ============================================================================
# 5. LENTES DE LUZ sacadas de la propia piel
# ============================================================================
def caja_solida(nombre, x0, x1, y0, y1, z0, z1):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    ob = nueva_malla(nombre, v, f)
    ob.hide_render = True
    return ob


def lente(cuerpo, nombre, cortador, mat, empuje):
    ob = cuerpo.copy()
    ob.data = cuerpo.data.copy()
    ob.name = nombre
    bpy.context.collection.objects.link(ob)
    booleano(ob, cortador, 'INTERSECT')
    if len(ob.data.vertices) == 0:
        bpy.data.objects.remove(ob, do_unlink=True)
        return None
    ob.data.transform(mathutils.Matrix.Translation(Vector(empuje)))
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    print(f"LENTE {nombre:12s} {len(ob.data.polygons)} caras")
    return ob


def luces(cuerpo, M, alto):
    piezas = []
    p = lente(cuerpo, "LuzTrasera",
              caja_solida("clt", LARGO_OBJ - 0.30, LARGO_OBJ + 0.05,
                          0.42 * alto, 0.52 * alto, -1.2, 1.2),
              M["luz_t"], (0.005, 0, 0))
    if p:
        piezas.append(p)
    for lado in (+1, -1):
        c = caja_solida(f"cld{lado}", -0.05, 0.26, 0.30 * alto, 0.375 * alto,
                        min(lado * 0.24, lado * 0.74), max(lado * 0.24, lado * 0.74))
        p = lente(cuerpo, f"LuzDel{lado}", c, M["luz_d"], (-0.005, 0, 0))
        if p:
            piezas.append(p)
    return piezas


# ============================================================================
# 6. MATERIALES, CHASIS Y ESTUDIO
# ============================================================================
def princ(nombre, **kw):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    for k, v in kw.items():
        if k in b.inputs:
            b.inputs[k].default_value = v
    return m


def emisivo(nombre, col, fuerza):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*col, 1)
    em.inputs["Strength"].default_value = fuerza
    nt.links.new(em.outputs["Emission"],
                 nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return m


def materiales():
    return {
        "pintura": princ("Pintura", **{"Base Color": (0.055, 0.060, 0.070, 1),
                                       "Metallic": 0.85, "Roughness": 0.20,
                                       "Coat Weight": 1.0, "Coat Roughness": 0.028}),
        "vidrio": princ("Vidrio", **{"Base Color": (0.02, 0.025, 0.032, 1),
                                     "Roughness": 0.04, "Transmission Weight": 0.88,
                                     "IOR": 1.52}),
        "negro": princ("Negro", **{"Base Color": (0.016, 0.018, 0.021, 1),
                                   "Roughness": 0.42}),
        "hule": princ("Hule", **{"Base Color": (0.013, 0.013, 0.015, 1),
                                 "Roughness": 0.78}),
        "rin": princ("Rin", **{"Base Color": (0.46, 0.48, 0.52, 1), "Metallic": 1.0,
                               "Roughness": 0.19}),
        "acero": princ("Acero", **{"Base Color": (0.36, 0.38, 0.42, 1),
                                   "Metallic": 0.9, "Roughness": 0.38}),
        "luz_t": emisivo("LuzT", (1.0, 0.05, 0.09), 5.0),
        "luz_d": emisivo("LuzD", (0.62, 0.85, 1.0), 6.0),
    }


def pintar(ob, M, alto):
    """Pintura / cristal / negro por zona. El límite del cristal se marca sobre la
    cintura y el faldón por altura relativa, que en un cascarón denso da un borde
    suficientemente limpio."""
    for k in ("pintura", "vidrio", "negro"):
        ob.data.materials.append(M[k])
    for p in ob.data.polygons:
        c = p.center
        fz = c.y / alto                                 # altura relativa
        if fz < 0.16:
            p.material_index = 2
        elif 0.30 < c.x < 2.30 and fz > 0.63 and p.normal.y > -0.30:
            p.material_index = 1
        else:
            p.material_index = 0
        p.use_smooth = True


def construir_chasis(M):
    obs = []
    for t in CH["tubos"]:
        A, B = Vector(t["a"]), Vector(t["b"])
        d = B - A
        L = d.length
        if L < 1e-6:
            continue
        s = t["sec"]
        if s["tipo"] == "redondo":
            R = s["d"] / 2
            perfil = [(R * math.cos(2 * math.pi * k / 12), R * math.sin(2 * math.pi * k / 12))
                      for k in range(12)]
        else:
            h = s["b"] / 2
            perfil = [(-h, -h), (h, -h), (h, h), (-h, h)]
        q = d.normalized().to_track_quat('Z', 'Y')
        n = len(perfil)
        verts = [tuple(q @ Vector((px, py, 0.0)) + A + d * t_) for t_ in (0.0, 1.0)
                 for (px, py) in perfil]
        faces = [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
        faces += [tuple(range(n)), tuple(reversed(range(n, 2 * n)))]
        o = nueva_malla("t", verts, faces)
        if s["tipo"] == "redondo":
            for p in o.data.polygons:
                p.use_smooth = True
        obs.append(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.join()
    ch = bpy.context.view_layer.objects.active
    ch.name = "Chasis"
    ch.data.materials.append(M["acero"])
    return ch


def area(nombre, pos, mira, w, h, pot, col=(1, 1, 1)):
    d = bpy.data.lights.new(nombre, 'AREA')
    d.shape, d.size, d.size_y, d.energy, d.color = 'RECTANGLE', w, h, pot, col
    o = bpy.data.objects.new(nombre, d)
    bpy.context.collection.objects.link(o)
    o.location = pos
    o.rotation_euler = (Vector(mira) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()


def estudio():
    m = princ("Piso", **{"Base Color": (0.055, 0.058, 0.065, 1), "Roughness": 0.33})
    piso = nueva_malla("Piso", [(-16, -16, 0), (20, -16, 0), (20, 16, 0), (-16, 16, 0)],
                       [(0, 1, 2, 3)])
    piso.data.materials.append(m)
    w = bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.020, 0.023, 0.029, 1)
    area("franja", (1.7, -0.7, 4.4), (1.7, 0, 0.5), 7.5, 1.1, 950)
    area("clave", (5.6, -5.0, 3.4), (1.6, 0, 0.5), 3.4, 3.4, 750)
    area("relleno", (-1.4, 5.0, 2.5), (1.7, 0, 0.5), 4.2, 3.0, 280, (0.80, 0.87, 1.0))
    area("contra", (-4.0, -1.6, 2.0), (1.5, 0, 0.6), 2.8, 2.4, 460, (1.0, 0.93, 0.85))


VISTAS = {
    "34frente": ((-4.60, -6.10, 1.35), (1.35, 0, 0.46), 78),
    "34atras": ((8.40, -5.80, 1.50), (1.95, 0, 0.48), 78),
    "lateral": ((1.68, -16.0, 0.66), (1.68, 0, 0.50), 120),
    "frontal": ((-14.0, 0.0, 0.72), (1.10, 0, 0.50), 120),
}


def render(nombre, vista, muestras):
    e = bpy.context.scene
    e.render.engine = 'CYCLES'
    e.cycles.device = 'CPU'
    e.cycles.samples = muestras
    e.cycles.use_denoising = True
    e.render.resolution_x, e.render.resolution_y = 1760, 990
    e.view_settings.view_transform = 'AgX'
    e.view_settings.look = 'AgX - Punchy'
    pos, mira, foc = VISTAS[vista]
    cd = bpy.data.cameras.new("c")
    cd.lens = foc
    c = bpy.data.objects.new("c", cd)
    bpy.context.collection.objects.link(c)
    c.location = pos
    c.rotation_euler = (Vector(mira) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    e.camera = c
    e.render.filepath = os.path.join(SALIDA, f"{nombre}-{vista}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDER OK", e.render.filepath)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = materiales()
    glb = os.path.join(RAIZ, arg("--glb", "cad/referencia-ia.glb"))
    cuerpo = cargar_ia(glb)
    d = reorientar(cuerpo)
    alto = d.y
    ok = validar_envolvente(cuerpo)

    # ORDEN CRITICO: todo lo que se EXTRAE sale del cuerpo integro. Encadenar los
    # cuatro cortes de paso de rueda antes deja la malla no-manifold y las
    # extracciones posteriores devuelven casi vacio (asi se perdia la puerta derecha).
    piezas_luz = luces(cuerpo, M, alto) if arg("--luces", "1") == "1" else []
    # El corte de puertas queda DESACTIVADO por defecto: la malla de la IA es un
    # solido cerrado, no un cascaron, asi que abrirle el hueco deja a la vista el
    # relleno macizo del volumen. Para tener gaviotas de verdad la carroceria tiene
    # que llevar espesor primero.
    puertas = separar_puertas(cuerpo, M) if arg("--puertas-corte", "0") == "1" else []
    if arg("--arcos", "1") == "1":
        for i, r in enumerate(CH["ruedas"]):
            lado = 1 if r["z"] > 0 else -1
            cil = cilindro(f"arco{i}", r["x"], r["R"] + 0.045,
                           min(lado * 0.44, lado * 1.7), max(lado * 0.44, lado * 1.7))
            booleano(cuerpo, cil, 'DIFFERENCE')
    print(f"ARCOS          recortados · cuerpo {len(cuerpo.data.polygons)} caras")
    pintar(cuerpo, M, alto)
    for pan, lado in puertas:
        pintar(pan, M, alto)
    abrir_puertas(puertas, float(arg("--puertas", "0")))

    ruedas = []
    for r in CH["ruedas"]:
        ruedas += rueda(r, M)
    chasis = construir_chasis(M)
    if arg("--chasis", "0") != "1":
        chasis.hide_render = True

    raiz = bpy.data.objects.new("Carro", None)
    bpy.context.collection.objects.link(raiz)
    raiz.rotation_euler = (math.pi / 2, 0, 0)
    for ob in list(bpy.context.collection.objects):
        if ob is raiz or ob.parent or ob.type != 'MESH' or ob.name == "Piso":
            continue
        ob.parent = raiz

    estudio()
    muestras = int(arg("--muestras", "64"))
    nombre = arg("--nombre", "final")
    for v in arg("--vistas", "34frente,lateral").split(","):
        render(nombre, v, muestras)
    destino = arg("--guardar", "")
    if destino:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(RAIZ, destino))
        print("BLEND GUARDADO", destino)
    print("VALIDACION:", "OK" if ok else "REVISAR")


main()
