# -*- coding: utf-8 -*-
"""
Carro v3 en Blender: superficie de subdivisión + detalle duro + contexto de escala.

Se corre SIN ventana:
    blender --background --python render/carro_v3.py -- [--rapido] [--muestras 96]
                                                        [--sin-render] [--sin-exportar]

Qué hace, en orden:
  1. Levanta la jaula de cad/carro-v3-jaula.json (calculos/carro3d_jaula.py) y le
     aplica Catmull-Clark nivel 3 con los creases de las líneas de carácter.
  2. Reparte materiales por región sobre la malla ya subdividida: pintura, cristal
     (canopy, cristal lateral, luneta), negro (faldón, bajos, cola).
  3. Corta con booleanos: pasos de rueda (con su pozo), boca de la parrilla, branquia
     lateral, y las juntas de la puerta de gaviota como ranura sobre la piel.
  4. Proyecta sobre la piel las firmas de luz de la lámina (cad/firma-luces.json) —
     la Y delantera y la barra + triángulo traseros — con Shrinkwrap, no con booleano.
  5. Agrega el detalle: malla de la parrilla, splitter, aletas del difusor, espejos,
     ruedas con rayos y frenos, butacas, tablero, volante y dos pilotos de 1.75 m.
  6. Exporta cad/carro-v3.glb (todo, con materiales), cad/carro-v3-carroceria-mm.stl
     (sólo la carrocería, en mm) y cad/carro-v3.blend.
  7. Renderiza en Cycles (GPU) las vistas ortográficas con fondo transparente para
     compararlas contra la referencia (render/comparar_v3.py) y dos tres cuartos.

Convención del proyecto: X largo, Y ALTO, Z lateral. Blender asume Z-arriba, así que
las cámaras se arman con matriz a mano (ver fotos.py); lo demás no se entera.
"""
import json
import math
import os
import sys
from math import cos, pi, sin

import bpy
import bmesh
import mathutils
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d


RAPIDO = "--rapido" in ARGS
SOLO_VISTAS = arg("--vistas", "").split(",") if arg("--vistas") else None
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAD = os.path.join(RAIZ, "cad")
SAL = arg("--salida") or os.path.join(RAIZ, "render", "salida", "v3")
os.makedirs(SAL, exist_ok=True)

J = json.load(open(os.path.join(CAD, "carro-v3-jaula.json"), encoding="utf-8"))
LUCES = json.load(open(os.path.join(CAD, "firma-luces.json"), encoding="utf-8"))
PQ = J["paquete"]
X_MORRO, X_COLA, SEMI, ALTO = PQ["x_morro"], PQ["x_cola"], PQ["semi"], PQ["alto"]
X_CANOPY0, X_CANOPY1 = PQ["x_canopy"]
X_LUNETA0, X_LUNETA1 = PQ["x_luneta"]
Y_PISO = PQ["y_piso"]
Y_BARRA = 0.572                 # arista de la cola: ahí va la barra de luz trasera

# ---- escena limpia -----------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
ESCENA = bpy.context.scene
COL = bpy.context.collection
MODELO = []                      # objetos que van al GLB (no luces, piso ni cámaras)
CUERPO = None


# ============================================================================
# 0. Utilería de malla
# ============================================================================
def objeto(nombre, verts, faces, mat=None, suave=True, modelo=True):
    me = bpy.data.meshes.new(nombre)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    ob = bpy.data.objects.new(nombre, me)
    COL.objects.link(ob)
    if mat is not None:
        me.materials.append(mat)
    if suave:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    if modelo:
        MODELO.append(ob)
    return ob


def normales(ob):
    """Normales consistentes y HACIA AFUERA. recalc_face_normals sólo garantiza
    consistencia; si el volumen firmado sale negativo, el sólido está al revés y el
    booleano exacto lo lee como el complemento del universo."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bm.calc_volume(signed=True) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()


def volumen(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    v = bm.calc_volume(signed=True)
    bm.free()
    return v


def activar(ob):
    # los objetos recién ligados no aparecen en la capa hasta que se sincroniza; sin
    # esto la iteración devuelve None en modo background
    bpy.context.view_layer.update()
    for o in bpy.context.view_layer.objects:
        if o is not None:
            o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def aplicar(ob, mod):
    activar(ob)
    bpy.ops.object.modifier_apply(modifier=mod.name)


def suavizar_por_angulo(ob, grados=35):
    activar(ob)
    try:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(grados))
    except Exception:
        bpy.ops.object.shade_smooth()


def borrar(ob):
    bpy.data.objects.remove(ob, do_unlink=True)


def barrido(puntos, seccion, cerrar=True):
    """Barre un polígono 2D (u,v) a lo largo de una polilínea 3D. Marco por transporte
    paralelo: no se retuerce en las curvas. Devuelve (verts, faces) cerrados."""
    P = [Vector(p) for p in puntos]
    T = [(P[i + 1] - P[i]).normalized() for i in range(len(P) - 1)]
    Tm = [T[0]]
    for i in range(1, len(T)):
        s = T[i - 1] + T[i]
        Tm.append(s.normalized() if s.length > 1e-6 else T[i])
    Tm.append(T[-1])
    n0 = Vector((0, 0, 1)) if abs(Tm[0].z) < 0.9 else Vector((0, 1, 0))
    N = (n0 - Tm[0] * n0.dot(Tm[0])).normalized()
    verts, faces, anillos = [], [], []
    for i, p in enumerate(P):
        if i > 0:
            N = (N - Tm[i] * N.dot(Tm[i]))
            N.normalize()
        B = Tm[i].cross(N)
        ring = []
        for (u, v) in seccion:
            ring.append(len(verts))
            verts.append(tuple(p + u * N + v * B))
        anillos.append(ring)
    m = len(seccion)
    for i in range(len(anillos) - 1):
        for k in range(m):
            faces.append((anillos[i][k], anillos[i][(k + 1) % m],
                          anillos[i + 1][(k + 1) % m], anillos[i + 1][k]))
    if cerrar:
        faces.append(tuple(reversed(anillos[0])))
        faces.append(tuple(anillos[-1]))
    return verts, faces


def tubo(puntos, r, n=10):
    return barrido(puntos, [(r * cos(2 * pi * k / n), r * sin(2 * pi * k / n)) for k in range(n)])


def revolucion(perfil, centro, n=64, invertir=False):
    """Revoluciona un lazo cerrado (radio, avance-en-z) alrededor del eje z que pasa
    por `centro`. `invertir` espeja el avance (rueda del otro lado)."""
    cx, cy, cz = centro
    s = -1 if invertir else 1
    verts, faces = [], []
    m = len(perfil)
    for k in range(n):
        a = 2 * pi * k / n
        for (r, w) in perfil:
            verts.append((cx + r * cos(a), cy + r * sin(a), cz + s * w))
    for k in range(n):
        k2 = (k + 1) % n
        for j in range(m):
            j2 = (j + 1) % m
            faces.append((k * m + j, k * m + j2, k2 * m + j2, k2 * m + j))
    return verts, faces


def cilindro(r, c, largo, n=48):
    """Cilindro sólido tapado, eje z, centrado en c."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=n, radius1=r, radius2=r, depth=largo)
    verts = [(c[0] + v.co.x, c[1] + v.co.y, c[2] + v.co.z) for v in bm.verts]
    bm.verts.ensure_lookup_table()
    faces = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    return verts, faces


def caja(c, d, rot=None):
    """Caja centrada en c con dimensiones d (dx,dy,dz), rotada por una matriz opcional."""
    x, y, z = d[0] / 2, d[1] / 2, d[2] / 2
    vs = [Vector((sx * x, sy * y, sz * z)) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    if rot is not None:
        vs = [rot @ v for v in vs]
    vs = [tuple(Vector(c) + v) for v in vs]
    fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return vs, fs


def esfera(c, r, n=16, escala=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=2 * n, v_segments=n, radius=r)
    verts = [(c[0] + v.co.x * escala[0], c[1] + v.co.y * escala[1], c[2] + v.co.z * escala[2])
             for v in bm.verts]
    bm.verts.ensure_lookup_table()
    faces = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    return verts, faces


def chaikin(pts, veces=1):
    """Suaviza un contorno cerrado (corta esquinas). Los contornos vectorizados de la
    lámina vienen con escalones de píxel; sin esto la luz sale dentada."""
    for _ in range(veces):
        out = []
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            out.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            out.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        pts = out
    return pts


def poligono_plano(pts2d, eje, coord, cortes=4):
    """Malla plana de un polígono 2D subdividida (para poder envolverla sobre la piel).
    eje: 'x' -> puntos (z,y) en el plano x=coord; 'z' -> puntos (x,y) en z=coord;
    'y' -> puntos (x,z) en y=coord. El relleno es por triangulación del contorno,
    que sí aguanta polígonos cóncavos (un n-gon no)."""
    def v3(p):
        if eje == "x":
            return (coord, p[1], p[0])
        if eje == "z":
            return (p[0], p[1], coord)
        return (p[0], coord, p[1])
    limpio = []
    for p in pts2d:
        if not limpio or (abs(p[0] - limpio[-1][0]) + abs(p[1] - limpio[-1][1])) > 1e-4:
            limpio.append(p)
    if (abs(limpio[0][0] - limpio[-1][0]) + abs(limpio[0][1] - limpio[-1][1])) < 1e-4:
        limpio.pop()
    bm = bmesh.new()
    vs = [bm.verts.new(v3(p)) for p in limpio]
    es = [bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=es)
    for _ in range(cortes):
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=False)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.ensure_lookup_table()
    verts = [tuple(v.co) for v in bm.verts]
    faces = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    return verts, faces


def envolver(ob, objetivo, eje, desplaz, plano=None, afuera=None):
    """Shrinkwrap por proyección a lo largo de un eje, en ambos sentidos.

    Lo que no encuentra piel se queda en el plano de origen y arma picos de metros
    al unirse con lo que sí proyectó: esos vértices se borran. Y las normales se
    orientan hacia `afuera` (vector), que es lo que Solidify usa para crecer."""
    m = ob.modifiers.new("envolver", "SHRINKWRAP")
    m.wrap_method = "PROJECT"
    m.wrap_mode = "ON_SURFACE"
    m.target = objetivo
    m.use_negative_direction = True
    m.use_positive_direction = True
    m.use_project_x = eje == "x"
    m.use_project_y = eje == "y"
    m.use_project_z = eje == "z"
    m.offset = desplaz
    aplicar(ob, m)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    if plano is not None:
        k = {"x": 0, "y": 1, "z": 2}[eje]
        sueltos = [v for v in bm.verts if abs(v.co[k] - plano) < 1e-4]
        if sueltos:
            bmesh.ops.delete(bm, geom=sueltos, context="VERTS")
    if afuera is not None:
        bm.normal_update()
        malas = [f for f in bm.faces if f.normal.dot(Vector(afuera)) < 0]
        if malas:
            bmesh.ops.reverse_faces(bm, faces=malas)
    bm.to_mesh(ob.data)
    bm.free()
    return len(ob.data.vertices)


def solidificar(ob, espesor, hacia=1.0):
    m = ob.modifiers.new("solid", "SOLIDIFY")
    m.thickness = espesor
    m.offset = hacia
    # NUNCA "even offset": en las esquinas agudas (las Y de luz, los bolsillos)
    # escala el espesor por 1/sin y dispara picos de metros
    m.use_even_offset = False
    aplicar(ob, m)
    # con offset positivo Solidify deja el cascarón con las normales hacia adentro, y
    # el booleano exacto lee eso como "todo el universo menos el cortador"
    normales(ob)


def booleano(ob, cortador, op="DIFFERENCE", transferir=True, auto=False, callado=False):
    m = ob.modifiers.new("bool", "BOOLEAN")
    m.operation = op
    m.solver = "EXACT"
    m.use_self = auto
    m.object = cortador
    m.material_mode = "TRANSFER" if transferir else "INDEX"
    antes = len(ob.data.vertices)
    aplicar(ob, m)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    bm.free()
    if not callado:
        print(f"  bool {op} {cortador.name}: {antes} -> {len(ob.data.vertices)} vertices, "
              f"{nm} aristas no manifold, volumen {volumen(ob):+.3f} (cortador {volumen(cortador):+.3f})")
    if len(ob.data.vertices) < 0.5 * antes:
        raise RuntimeError(f"el booleano con {cortador.name} destruyo la malla")


def dentro(p, poli):
    """Punto en polígono (par-impar)."""
    x, y = p
    adentro = False
    n = len(poli)
    for i in range(n):
        x1, y1 = poli[i]
        x2, y2 = poli[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xi:
                adentro = not adentro
    return adentro


def rayo(ob, origen, direccion):
    ok, pos, nor, _ = ob.ray_cast(Vector(origen), Vector(direccion).normalized())
    return (Vector(pos), Vector(nor)) if ok else (None, None)


# ============================================================================
# 1. Materiales
# ============================================================================
def material(nombre, base, rug=0.5, metal=0.0, coat=0.0, emis=None, fuerza=0.0,
             trans=0.0, alpha=1.0, coat_rug=0.03):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1.0)
    b.inputs["Roughness"].default_value = rug
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = coat_rug
    if emis is not None:
        b.inputs["Emission Color"].default_value = (*emis, 1.0)
        b.inputs["Emission Strength"].default_value = fuerza
    if trans > 0:
        b.inputs["Transmission Weight"].default_value = trans
        b.inputs["IOR"].default_value = 1.5
    b.inputs["Alpha"].default_value = alpha
    if alpha < 1.0:
        m.surface_render_method = "BLENDED"
    m.diffuse_color = (*(emis if emis else base), alpha)
    m.metallic, m.roughness = metal, rug
    return m


def srgb(r, g, b):
    def f(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b))


MAT = {
    # pintura muestreada de la lámina del dueño (sRGB 115,106,102), con clearcoat
    # satinada: el doc maestro pide wrap satinado (perdona ondulaciones). Con clearcoat
    # 1.0 la piel reflejaba el estudio como espejo y cada ondita se leía como defecto.
    "pintura": material("pintura", srgb(84, 76, 72), rug=0.42, metal=0.45, coat=0.35,
                        coat_rug=0.18),
    "vidrio": material("vidrio", (0.30, 0.33, 0.36), rug=0.02, trans=1.0, coat=0.0),
    "negro": material("negro", srgb(18, 17, 17), rug=0.55),
    "negro_brillo": material("negro_brillo", srgb(12, 12, 12), rug=0.18, coat=0.8),
    "pozo": material("pozo", srgb(10, 10, 10), rug=0.9),
    "luz_d": material("luz_d", (0.75, 0.90, 1.0), rug=0.2, emis=(0.75, 0.9, 1.0), fuerza=2.2),
    "luz_t": material("luz_t", (1.0, 0.05, 0.02), rug=0.2, emis=(1.0, 0.06, 0.02), fuerza=3.5),
    "llanta": material("llanta", srgb(22, 22, 22), rug=0.85),
    # grafito satinado: el cromo hacía ver el rin de 13" como de carrito de golf
    "rin": material("rin", srgb(92, 94, 98), rug=0.32, metal=0.9),
    "hub": material("hub", srgb(60, 60, 62), rug=0.4, metal=0.8),
    "disco": material("disco", srgb(120, 118, 115), rug=0.45, metal=0.9),
    "caliper": material("caliper", srgb(170, 30, 20), rug=0.4),
    "cuero": material("cuero", srgb(150, 78, 40), rug=0.6),
    "interior": material("interior", srgb(32, 30, 28), rug=0.8),
    "piloto": material("piloto", srgb(48, 48, 52), rug=0.8),
    "malla": material("malla", srgb(28, 28, 28), rug=0.35, metal=0.6),
    "piso": material("piso", (0.045, 0.048, 0.055), rug=0.42),
}

# ============================================================================
# 2. CARROCERÍA — jaula + subdivisión + materiales por región
# ============================================================================
N_MEDIA = J["n_media"]
N_RING = 2 * N_MEDIA - 2
ESTACIONES = J["estaciones"]
CANOPY = J["cristal"]["canopy"]
LUNETA = J["cristal"]["luneta"]
Y_DLO = J["cristal"]["y_dlo"]


def interp(tabla, x):
    xs = [t[0] for t in tabla]
    ys = [t[1] for t in tabla]
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            t = (x - xs[i]) / (xs[i + 1] - xs[i])
            return ys[i] + t * (ys[i + 1] - ys[i])
    return ys[-1]


def x_parabrisas(z):
    """Base del parabrisas en planta: una V suave con la punta en el centro."""
    return 0.80 + 0.17 * (abs(z) / 0.62) ** 2


def material_carroceria(anillo, estacion, c):
    """Material de una cara de la piel subdividida por su anillo, la estación de la
    jaula de la que viene y su centro. Los bordes del cristal van alineados a la
    jaula (anillo 8 = base del cristal; estaciones = frente/fondo de cada cristal)
    para que salgan limpios y no escalonados."""
    x, y, z = c.x, c.y, abs(c.z)
    x0 = ESTACIONES[estacion] if 0 <= estacion < len(ESTACIONES) else x
    x1 = ESTACIONES[estacion + 1] if 0 <= estacion + 1 < len(ESTACIONES) else x
    if anillo == -2:                                   # tapa de la cola
        return "pintura"
    if anillo == -1:                                   # tapa de la nariz
        return "pintura"
    if anillo >= 8:
        # canopy: del parabrisas (V en planta) al fin del techo de cristal (2.22)
        if x >= x_parabrisas(z) and x1 <= 2.221:
            return "vidrio"
        # cristal de cuarto: los dos anillos bajos siguen una estación más (2.36)
        if anillo <= 9 and 2.21 < x0 and x1 <= 2.361:
            return "vidrio"
        # luneta: entre las estaciones 2.50 y 2.92, anillo 8 ya es su borde
        if x0 >= 2.499 and x1 <= 2.921:
            return "vidrio"
    if anillo <= 1:
        return "negro"                                 # bajos
    # el faldón y la cola van en color carrocería: lo negro (difusor) es un bolsillo
    # real cortado con booleano, no una pintada por altura que dejaba escalones
    return "pintura"


def carroceria():
    verts, faces = J["verts"], J["faces"]
    me = bpy.data.meshes.new("Carroceria")
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    ob = bpy.data.objects.new("Carroceria", me)
    COL.objects.link(ob)
    MODELO.append(ob)
    # anillo y estación viajan como atributos de cara: el modificador de subdivisión
    # los hereda a las caras hijas (verificado en 4.5)
    at_an = me.attributes.new("anillo", "INT", "FACE")
    at_es = me.attributes.new("estacion", "INT", "FACE")
    for i, (a, e, x) in enumerate(J["attr"]):
        at_an.data[i].value = a
        at_es.data[i].value = e
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    # creases
    cr = me.attributes.new("crease_edge", "FLOAT", "EDGE")
    idx = {tuple(sorted(e.vertices)): e.index for e in me.edges}
    for a, b, w in J["creases"]:
        k = tuple(sorted((a, b)))
        if k in idx:
            cr.data[idx[k]].value = max(cr.data[idx[k]].value, w)
    normales(ob)
    m = ob.modifiers.new("subdiv", "SUBSURF")
    m.levels = m.render_levels = 2 if RAPIDO else 3
    m.use_creases = True
    aplicar(ob, m)
    # materiales reales por región
    slots = list(MAT.keys())
    me = ob.data
    anillos = [d.value for d in me.attributes["anillo"].data]
    estaciones = [d.value for d in me.attributes["estacion"].data]
    me.materials.clear()
    for s in ("pintura", "vidrio", "negro", "pozo", "negro_brillo"):
        me.materials.append(MAT[s])
    nombres = [s.name for s in me.materials]
    conteo = {}
    for f, an, es in zip(me.polygons, anillos, estaciones):
        nom = material_carroceria(an, es, f.center)
        f.material_index = nombres.index(nom)
        conteo[nom] = conteo.get(nom, 0) + 1
    print("  caras por material:", conteo)
    normales(ob)
    bm = bmesh.new()
    bm.from_mesh(me)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    bm.free()
    print(f"CARROCERIA  {len(me.polygons)} caras tras subdividir, volumen {volumen(ob):+.3f}, "
          f"{nm} aristas no manifold")
    return ob


# ============================================================================
# 3. Cortes: pasos de rueda, parrilla, branquia, juntas de puerta
# ============================================================================
def pasos_de_rueda(cuerpo):
    for w in J["ruedas"]:
        R = w["R"] + 0.046
        lado = 1 if w["z"] > 0 else -1
        # el pozo arranca en |z|=0.615: el larguero fx_lo-dash_lo corre en z=0.53-0.60
        # (PTR 38) y con el pozo en 0.55 quedaba dentro de la cavidad (auditoría
        # 2026-09-05). La cara interior de la llanta está en 0.66: quedan 45 mm.
        Z_POZO = 0.615
        vs, fs = cilindro(R, (w["x"], w["R"], lado * (Z_POZO + 1.15) / 2), 1.15 - Z_POZO, n=72)
        cortador = objeto("_paso", vs, fs, MAT["pozo"], modelo=False)
        normales(cortador)
        booleano(cuerpo, cortador)
        borrar(cortador)


def boca_parrilla(cuerpo):
    """Boca ancha bajo el labio del cofre, entre las uniones de las Y de luz."""
    poli = [(-0.74, 0.31), (-0.55, 0.30), (0.0, 0.285), (0.55, 0.30), (0.74, 0.31),
            (0.78, 0.25), (0.72, 0.14), (0.0, 0.135), (-0.72, 0.14), (-0.78, 0.25)]
    return bolsillo(cuerpo, poli, "x", X_MORRO - 0.6, 0.055, "pozo")


def branquias(cuerpo):
    """Branquia tipo 33 Stradale: gancho detrás de la rueda delantera que corre por
    encima del faldón hasta la rueda trasera. Un bolsillo somero en cada flanco."""
    poli = [(0.96, 0.56), (1.00, 0.58), (1.05, 0.53), (1.13, 0.40), (1.23, 0.32),
            (1.30, 0.29), (2.30, 0.29), (2.30, 0.25), (1.22, 0.25), (1.12, 0.27),
            (1.03, 0.36), (0.97, 0.47)]
    for lado in (1, -1):
        bolsillo(cuerpo, poli, "z", lado * (SEMI + 0.5), 0.022, "negro", dir_neg=lado < 0)


def boca_difusor(cuerpo):
    """Difusor como en la lámina trasera: banda negra hundida bajo la barra de luz que
    deja en color carrocería una V alrededor del triángulo y las dos esquinas de la
    cadera. Puntos (z, y) vistos desde atrás. Se queda en |z|<=0.70: más afuera el
    bolsillo rompería hacia el pozo de la rueda (que llega a x=3.03)."""
    der = [(0.186, 0.525), (0.60, 0.525), (0.67, 0.505), (0.70, 0.45), (0.70, 0.24),
           (0.66, 0.175)]
    poli = [(0.0, 0.205)] + der + [(-z, y) for z, y in der[::-1]]
    return bolsillo(cuerpo, poli, "x", X_COLA + 0.6, 0.05, "negro", dir_neg=False,
                    afuera_x=1)


def bolsillo(cuerpo, poli2d, eje, plano, hondo, mat, dir_neg=False, afuera_x=-1, suavizar=2):
    """Hunde un polígono proyectado `hondo` metros en la piel. El fondo sigue la
    superficie (Shrinkwrap con desplazamiento negativo) y las paredes salen rectas
    hacia afuera; se resta con booleano y las caras nuevas llevan `mat`."""
    vs, fs = poligono_plano(chaikin(poli2d, suavizar) if suavizar else poli2d, eje, plano, cortes=3)
    ob = objeto("_bolsillo", vs, fs, MAT[mat], modelo=False)
    afuera = {"x": (afuera_x, 0, 0), "z": (0, 0, -1 if dir_neg else 1), "y": (0, 1, 0)}[eje]
    # el fondo se proyecta SOBRE la piel y luego se corre `hondo` a lo largo del eje.
    # Con el desplazamiento de Shrinkwrap (que va por la normal) el contorno se movía
    # de lado en las zonas curvas y la orilla del bolsillo salía ondulada.
    n = envolver(ob, cuerpo, eje, 0.0, plano=plano, afuera=afuera)
    if n < 4:
        borrar(ob)
        return
    for v in ob.data.vertices:
        v.co -= Vector(afuera) * hondo
    # prisma: el fondo envuelto se conserva (use_keep_orig) y su copia se corre a lo
    # largo del eje hacia afuera, con paredes rectas
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    r = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:] + bm.edges[:] + bm.verts[:],
                                      use_keep_orig=True)
    vnew = [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=vnew, vec=Vector(afuera) * 0.8)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bm.calc_volume(signed=True) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()
    booleano(cuerpo, ob)
    borrar(ob)


def tapar_agujeros(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    # los booleanos dejan vértices casi coincidentes en las puntas: se sueldan antes
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=2e-4)
    borde = [e for e in bm.edges if e.is_boundary]
    if borde:
        bmesh.ops.holes_fill(bm, edges=borde, sides=64)
        print(f"  agujeros: {len(borde)} aristas de borde tapadas")
    bm.to_mesh(ob.data)
    bm.free()


def limpiar(ob):
    """Se queda con el componente conexo más grande: los booleanos dejan a veces
    trocitos del cortador flotando."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    visto = [False] * len(bm.verts)
    grupos = []
    for v0 in bm.verts:
        if visto[v0.index]:
            continue
        pila, grupo = [v0], []
        visto[v0.index] = True
        while pila:
            v = pila.pop()
            grupo.append(v)
            for e in v.link_edges:
                o = e.other_vert(v)
                if not visto[o.index]:
                    visto[o.index] = True
                    pila.append(o)
        grupos.append(grupo)
    grupos.sort(key=len, reverse=True)
    basura = [v for g in grupos[1:] for v in g]
    if basura:
        bmesh.ops.delete(bm, geom=basura, context="VERTS")
        print(f"  limpieza: {len(grupos) - 1} trozos sueltos ({len(basura)} vertices) fuera")
    bm.to_mesh(ob.data)
    bm.free()


def cinta_sobre_piel(nombre, polilinea2d, eje, plano, ancho, mat, afuera, cerrada=False):
    """Franja de `ancho` que sigue una polilínea 2D proyectada sobre la piel: se
    construye el contorno desplazando la línea ±ancho/2 en su plano, se envuelve con
    Shrinkwrap y se le da 1 mm de espesor. Sirve para las juntas de panel: una línea
    negra de 5 mm sobre la pintura se lee como junta y no toca la malla del cuerpo,
    que sigue siendo un sólido limpio para el STL."""
    # densificar para que siga la curvatura
    dens = []
    for a, b in zip(polilinea2d[:-1], polilinea2d[1:]):
        n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.02))
        for k in range(n):
            t = k / n
            dens.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
    dens.append(polilinea2d[-1])
    izq, der = [], []
    for i, p in enumerate(dens):
        a = dens[max(i - 1, 0)]
        b = dens[min(i + 1, len(dens) - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / L * ancho / 2, tx / L * ancho / 2
        izq.append((p[0] + nx, p[1] + ny))
        der.append((p[0] - nx, p[1] - ny))
    poli = izq + der[::-1]
    vs, fs = poligono_plano(poli, eje, plano, cortes=0)
    ob = objeto(nombre, vs, fs, MAT[mat])
    envolver(ob, CUERPO, eje, 0.0006, plano=plano, afuera=afuera)
    solidificar(ob, 0.0012, hacia=1.0)
    return ob


def juntas_de_puerta(cuerpo):
    """Contorno de la puerta de gaviota como junta de 6 mm sobre la piel. Adelante
    sigue el pilar A, arriba corre por el espinazo (|z|=0.15, el eje de bisagra del
    chasis) y atrás baja por la pierna del arco. Dos proyecciones: los flancos desde
    el costado y el techo desde arriba."""
    lado_xy = [(1.06, 0.30), (1.08, 0.40), (1.13, 0.52), (1.21, 0.66), (1.31, 0.80),
               (1.43, 0.92), (1.56, 0.99)]
    techo_xz = [(1.50, 0.50), (1.55, 0.40), (1.60, 0.28), (1.66, 0.18), (1.72, 0.15),
                (1.98, 0.15), (2.04, 0.18), (2.10, 0.28), (2.15, 0.40), (2.19, 0.50)]
    tras_xy = [(2.12, 0.99), (2.16, 0.90), (2.19, 0.76), (2.19, 0.60), (2.16, 0.45),
               (2.14, 0.30)]
    piso_xy = [(2.14, 0.30), (1.06, 0.30)]
    for lado in (1, -1):
        cinta_sobre_piel("JuntaPuerta", lado_xy, "z", lado * (SEMI + 0.5), 0.006, "negro",
                         (0, 0, lado))
        cinta_sobre_piel("JuntaPuerta", tras_xy + piso_xy, "z", lado * (SEMI + 0.5), 0.006,
                         "negro", (0, 0, lado))
        cinta_sobre_piel("JuntaPuerta", [(x, lado * z) for x, z in techo_xz], "y", 2.0, 0.006,
                         "negro", (0, 1, 0))


# ============================================================================
# 4. Luces proyectadas desde la lámina
# ============================================================================
def _triangulo_trasero(dy):
    """Anillo triangular invertido (en u,v del frente) centrado bajo la barra."""
    yc = (Y_BARRA - 0.155 - dy) / ALTO
    def tri(lado):
        h = lado * 0.86
        return [(-lado / 2 / SEMI, (yc + h / 3)), (lado / 2 / SEMI, (yc + h / 3)),
                (0.0, (yc - 2 * h / 3))]
    ext, inte = tri(0.26), tri(0.16)
    # [0:3] triángulo exterior (luz); [4:7] interior (malla negra encima)
    return [ext[0], ext[1], ext[2], ext[0], inte[0], inte[1], inte[2]]


# Ejes de las firmas de luz en (u, v) de la lámina (u = z/SEMI, v = y/ALTO), lado +z.
# Se trazaron sobre los contornos de cad/firma-luces.json: la lámina las dibuja de
# 35-55 mm de grueso porque el contorno incluye el resplandor; la luz en sí es una
# línea de ~22 mm.
EJES_LUZ_DEL = [
    [(0.897, 0.600), (0.893, 0.550), (0.880, 0.490), (0.862, 0.430), (0.845, 0.380),
     (0.828, 0.356), (0.780, 0.348), (0.700, 0.338), (0.600, 0.326), (0.520, 0.313)],
    [(0.842, 0.325), (0.858, 0.290), (0.878, 0.255), (0.905, 0.212)],
]
EJES_LUZ_TRAS = [
    [(0.435, 0.497), (0.650, 0.495), (0.710, 0.488), (0.760, 0.462), (0.800, 0.452),
     (0.845, 0.458)],
]
# la central baja a la cara de la cola: a la altura de las laterales caía justo en la
# arista y se veía de canto
EJE_BARRA_CENTRO = [(-0.25, 0.474), (0.25, 0.474)]


def _densificar(pts, paso):
    out = []
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / paso))
        out += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n)]
    return out + [pts[-1]]


def ranura_sobre_piel(cuerpo, linea_zy, x_cam, ancho, hondo, mat, cerrada=False):
    """Surco de ancho constante que sigue la piel. Cada punto del eje se proyecta
    sobre la piel con un rayo desde x_cam y ahí se arma una sección rectangular
    orientada por la NORMAL de la piel (no por el eje de proyección): así el ancho no
    se estira donde la superficie corre casi paralela al rayo. El prisma se resta con
    booleano y el surco hereda el material emisivo."""
    dir_rayo = Vector((1.0 if x_cam < 0 else -1.0, 0.0, 0.0))
    P, N = [], []
    for (z, y) in linea_zy:
        pos, nor = rayo(cuerpo, (x_cam, y, z), dir_rayo)
        if pos is None:
            continue
        if nor.dot(dir_rayo) > 0:
            nor = -nor
        P.append(pos)
        N.append(nor.normalized())
    if len(P) < 3:
        print(f"  ranura {mat}: sólo {len(P)} de {len(linea_zy)} puntos tocaron la piel")
        return
    ranura_3d(cuerpo, P, N, ancho, hondo, mat, cerrada)


def ranura_3d(cuerpo, P, N, ancho, hondo, mat, cerrada=False):
    """Resta de la piel un prisma rectangular barrido por los puntos P (sobre la piel)
    con la sección orientada por las normales N."""
    # normales suavizadas a lo largo del eje: la malla subdividida las trae con ruido
    for _ in range(3):
        if cerrada:
            N = [(N[k - 1] + 2 * N[k] + N[(k + 1) % len(N)]).normalized() for k in range(len(N))]
        else:
            N = [N[0]] + [(N[k - 1] + 2 * N[k] + N[k + 1]).normalized() for k in range(1, len(N) - 1)] + [N[-1]]
    n = len(P)
    verts, faces = [], []
    for i in range(n):
        if cerrada:
            T = (P[(i + 1) % n] - P[(i - 1) % n]).normalized()
        else:
            T = (P[min(i + 1, n - 1)] - P[max(i - 1, 0)]).normalized()
        S = T.cross(N[i]).normalized() * (ancho / 2)
        afuera, adentro = N[i] * 0.015, -N[i] * hondo
        verts += [tuple(P[i] + S + afuera), tuple(P[i] - S + afuera),
                  tuple(P[i] - S + adentro), tuple(P[i] + S + adentro)]
    tramos = n if cerrada else n - 1
    for i in range(tramos):
        a, b = 4 * i, 4 * ((i + 1) % n)
        for k in range(4):
            faces.append((a + k, a + (k + 1) % 4, b + (k + 1) % 4, b + k))
    if not cerrada:
        faces.append((3, 2, 1, 0))
        m = 4 * (n - 1)
        faces.append((m, m + 1, m + 2, m + 3))
    ob = objeto("_ranura", verts, faces, MAT[mat], modelo=False)
    normales(ob)
    if CORTADORES is not None:          # modo maqueta: el booleano lo hace manifold3d
        CORTADORES.append(ob)
        return
    booleano(cuerpo, ob)
    borrar(ob)


def luces(cuerpo):
    """Firmas de luz como SURCOS de 22 mm sobre la piel con el fondo emisivo. Antes eran
    calcas envueltas por proyección frontal y en las esquinas de la nariz (donde la piel
    corre casi paralela al rayo) salían anchas y con la orilla mordida. En la maqueta
    impresa quedan como surcos limpios para pintar o meter fibra óptica."""
    ANCHO, HONDO = 0.022, 0.010
    for eje in EJES_LUZ_DEL:
        for lado in (1, -1):
            pts = _densificar([(lado * u * SEMI, v * ALTO) for (u, v) in eje], 0.008)
            ranura_sobre_piel(cuerpo, pts, X_MORRO - 1.0, ANCHO, HONDO, "luz_d")
    # trasera: la barra cae en la arista de la cola
    vmax = max(v for p in LUCES["luz_trasera"] for (u, v) in p)
    dy = Y_BARRA + 0.006 - vmax * ALTO
    xc = X_COLA + 1.0
    ranura_sobre_piel(cuerpo, _densificar([(u * SEMI, v * ALTO + dy) for (u, v) in EJE_BARRA_CENTRO], 0.01),
                      xc, ANCHO * 0.8, HONDO, "luz_t")
    for eje in EJES_LUZ_TRAS:
        for lado in (1, -1):
            pts = _densificar([(lado * u * SEMI, v * ALTO + dy) for (u, v) in eje], 0.008)
            ranura_sobre_piel(cuerpo, pts, xc, ANCHO * 0.8, HONDO, "luz_t")
    # triángulo: bolsillo luminoso con un triángulo menor más hondo de malla encima,
    # así queda el anillo de luz. (Barrerlo como surco cerrado se auto-intersecaba en
    # las esquinas de 60° y dejaba la malla abierta.) La cola ahí es casi normal a x,
    # así que la proyección no estira nada.
    tri = _triangulo_trasero(dy)
    for pts, mat, h in ((tri[0:3], "luz_t", HONDO), (tri[4:7], "malla", HONDO + 0.008)):
        zy = [(u * SEMI, v * ALTO + dy) for (u, v) in pts]
        zy = chaikin(_densificar(zy + [zy[0]], 0.02)[:-1], 1)
        bolsillo(cuerpo, zy, "x", X_COLA + 0.5, h, mat, afuera_x=1, suavizar=0)


# ============================================================================
# 5. Detalle duro
# ============================================================================
def malla_parrilla(cuerpo):
    """Retícula de rombos dentro de la boca: cintas planas envueltas sobre el fondo
    del bolsillo y con espesor. Dos familias a ±40°."""
    poli = [(-0.72, 0.305), (0.0, 0.29), (0.72, 0.305), (0.75, 0.24), (0.70, 0.15),
            (0.0, 0.145), (-0.70, 0.15), (-0.75, 0.24)]
    vs_all, fs_all = [], []
    paso, ancho = 0.055, 0.006
    for ang in (40, -40):
        a = math.radians(ang)
        d = (cos(a), sin(a))
        nrm = (-sin(a), cos(a))
        for k in range(-40, 41):
            off = k * paso
            c0 = (off * nrm[0], 0.22 + off * nrm[1])
            tramo = []
            for t in [i * 0.01 for i in range(-120, 121)]:
                p = (c0[0] + t * d[0], c0[1] + t * d[1])
                if dentro(p, poli):
                    tramo.append(p)
                elif tramo:
                    break_ = tramo
                    tramo = []
                    if len(break_) > 2:
                        _cinta(break_, nrm, ancho, vs_all, fs_all)
            if len(tramo) > 2:
                _cinta(tramo, nrm, ancho, vs_all, fs_all)
    ob = objeto("Parrilla", vs_all, fs_all, MAT["malla"])
    envolver(ob, cuerpo, "x", 0.012, plano=X_MORRO - 0.5, afuera=(-1, 0, 0))
    solidificar(ob, 0.005, hacia=1.0)


def _cinta(pts, nrm, ancho, vs, fs):
    base = len(vs)
    for (z, y) in pts:
        vs.append((X_MORRO - 0.5, y - nrm[1] * ancho / 2, z - nrm[0] * ancho / 2))
        vs.append((X_MORRO - 0.5, y + nrm[1] * ancho / 2, z + nrm[0] * ancho / 2))
    for i in range(len(pts) - 1):
        fs.append((base + 2 * i, base + 2 * i + 1, base + 2 * i + 3, base + 2 * i + 2))


def splitter(cuerpo):
    """Labio delantero: la planta del morro a y=0.16 desplazada 45 mm hacia afuera."""
    contorno = []
    for i in range(0, 61):
        z = -0.74 + 1.48 * i / 60           # sin llegar a las ruedas (z=0.66)
        p, n = rayo(cuerpo, (X_MORRO - 1.0, 0.165, z), (1, 0, 0))
        if p and p.x < 0.45:
            contorno.append((p.x - 0.045, z))
    if len(contorno) < 5:
        return
    # el borde por rayos sale con escalones de la malla: se suaviza a lo largo de z
    xs = [c[0] for c in contorno]
    for _ in range(6):
        xs = [xs[0]] + [0.25 * xs[k - 1] + 0.5 * xs[k] + 0.25 * xs[k + 1]
                        for k in range(1, len(xs) - 1)] + [xs[-1]]
    contorno = [(x, c[1]) for x, c in zip(xs, contorno)]
    xmax = max(c[0] for c in contorno) + 0.25
    poli = [(xmax, contorno[0][1])] + contorno + [(xmax, contorno[-1][1])]
    # cara inferior EN el plano del piso de la piel: en la maqueta impresa nace de la
    # cama en vez de quedar como voladizo de 0.8 mm que pide soporte
    vs, fs = poligono_plano(poli, "y", Y_PISO + 0.016, cortes=0)
    ob = objeto("Splitter", vs, fs, MAT["negro_brillo"])
    solidificar(ob, 0.016, hacia=-1.0)


def difusor(cuerpo, espesor=0.014, modelo=True):
    """Cuatro aletas verticales sobre el panel negro rebajado de la cola: cada una es
    un perfil (x,y) que sigue la piel por rayos y sobresale 45 mm."""
    hechas = []
    for z in (0.29, 0.49):
        for lado in (1, -1):
            perfil = []
            for y in (0.14, 0.20, 0.27, 0.34, 0.41):
                p, _ = rayo(cuerpo, (X_COLA + 1.0, y, lado * z), (-1, 0, 0))
                if p:
                    perfil.append((p.x - 0.03, y))
            if len(perfil) < 3:
                continue
            afuera = [(x + 0.045 + 0.02 * (i == 0), y) for i, (x, y) in enumerate(perfil)]
            poli = perfil + afuera[::-1]
            vs, fs = poligono_plano(poli, "z", lado * z - 0.007, cortes=0)
            ob = objeto("Aleta", vs, fs, MAT["negro"], suave=False, modelo=modelo)
            solidificar(ob, espesor, hacia=1.0)
            hechas.append(ob)
    return hechas


def espejos(cuerpo):
    """Cápsula aplanada sobre un brazo corto que nace de la repisa de la salpicadera,
    junto a la base del pilar A (como en la lámina)."""
    for lado in (1, -1):
        base, _ = rayo(cuerpo, (1.10, 2.0, lado * 0.72), (0, -1, 0))
        if base is None:
            base = Vector((1.10, 0.74, lado * 0.72))
        # gota alargada y baja (tipo ala), pegada a la repisa con un brazo corto e
        # inclinado; la paleta redonda sobre poste vertical se veía de los 60
        c = (base.x + 0.03, base.y + 0.030, lado * (abs(base.z) + 0.075))
        vs, fs = esfera(c, 0.080, n=14, escala=(1.35, 0.36, 0.52))
        objeto("Espejo", vs, fs, MAT["pintura"])
        vs, fs = barrido([(base.x - 0.02, base.y - 0.01, base.z),
                          (c[0] - 0.03, c[1] - 0.012, c[2] - lado * 0.035)],
                         [(-0.022, -0.005), (0.022, -0.005), (0.022, 0.005), (-0.022, 0.005)])
        objeto("Espejo_brazo", vs, fs, MAT["negro"], suave=False)


def ruedas():
    for w in J["ruedas"]:
        R, hw = w["R"], w["W"] / 2
        r_rin = 0.0254 * w["rin"] / 2
        lado = 1 if w["z"] > 0 else -1
        c = (w["x"], R, w["z"])
        perfil = [(R, -hw + 0.02), (R, hw - 0.02), (R - 0.012, hw), (R - 0.05, hw + 0.004),
                  (r_rin + 0.02, hw - 0.006), (r_rin, hw - 0.012), (r_rin, -hw + 0.012),
                  (r_rin + 0.02, -hw + 0.006), (R - 0.05, -hw - 0.004), (R - 0.012, -hw)]
        vs, fs = revolucion(perfil, c, n=72, invertir=lado < 0)
        ob = objeto("Llanta", vs, fs, MAT["llanta"])
        # barril del rin
        barril = [(r_rin + 0.002, hw - 0.010), (r_rin + 0.006, hw - 0.004),
                  (r_rin - 0.02, hw - 0.03), (r_rin - 0.02, -hw + 0.02),
                  (r_rin - 0.002, -hw + 0.02)]
        vs, fs = revolucion(barril, c, n=64, invertir=lado < 0)
        objeto("Rin", vs, fs, MAT["rin"])
        # cubo
        cubo = [(0.075, hw - 0.055), (0.075, hw - 0.035), (0.02, hw - 0.035), (0.02, hw - 0.055)]
        vs, fs = revolucion(cubo, c, n=32, invertir=lado < 0)
        objeto("Cubo", vs, fs, MAT["hub"])
        # 10 rayos torcidos, en pares
        for k in range(10):
            a0 = 2 * pi * k / 10 + (0.12 if k % 2 else -0.12)
            pts = []
            for t in [i / 6 for i in range(7)]:
                r = 0.06 + t * (r_rin - 0.026 - 0.06)
                a = a0 + math.radians(28) * t
                wz = (hw - 0.045) + t * 0.025 - 0.02 * math.sin(pi * t)
                pts.append((c[0] + r * cos(a), c[1] + r * sin(a), c[2] + lado * wz))
            vs, fs = barrido(pts, [(-0.011, -0.006), (0.011, -0.006), (0.011, 0.006), (-0.011, 0.006)])
            objeto("Rayo", vs, fs, MAT["rin"], suave=False)
        # disco y caliper
        disco = [(0.11, hw - 0.10), (0.11, hw - 0.08), (0.05, hw - 0.08), (0.05, hw - 0.10)]
        vs, fs = revolucion(disco, c, n=48, invertir=lado < 0)
        objeto("Disco", vs, fs, MAT["disco"])
        ang = math.radians(115)
        cc = (c[0] + 0.085 * cos(ang), c[1] + 0.085 * sin(ang), c[2] + lado * (hw - 0.09))
        rot = mathutils.Matrix.Rotation(ang, 4, "Z").to_3x3()
        vs, fs = caja(cc, (0.05, 0.085, 0.05), rot=rot)
        ob = objeto("Caliper", vs, fs, MAT["caliper"], suave=False)


def interior():
    # tablero
    vs, fs = caja((1.12, 0.66, 0.0), (0.32, 0.10, 1.10))
    objeto("Tablero", vs, fs, MAT["interior"], suave=False)
    vs, fs = caja((1.60, 0.36, 0.0), (1.10, 0.20, 0.22))          # túnel central
    objeto("Tunel", vs, fs, MAT["interior"], suave=False)
    vs, fs = caja((1.75, 0.20, 0.0), (1.40, 0.02, 1.20))          # piso de cabina
    objeto("PisoCabina", vs, fs, MAT["interior"], suave=False)
    for lado in (1, -1):
        zc = lado * 0.31
        vs, fs = caja((1.86, 0.27, zc), (0.50, 0.12, 0.42))       # cojín
        objeto("Butaca", vs, fs, MAT["cuero"], suave=False)
        rot = mathutils.Matrix.Rotation(math.radians(-24), 4, "Z").to_3x3()
        vs, fs = caja((2.08, 0.56, zc), (0.09, 0.52, 0.40), rot=rot)
        objeto("Respaldo", vs, fs, MAT["cuero"], suave=False)
        vs, fs = caja((2.16, 0.86, zc), (0.08, 0.14, 0.22), rot=rot)  # cabecera
        objeto("Cabecera", vs, fs, MAT["cuero"], suave=False)
    # volante del lado izquierdo (México)
    zc = 0.31
    cw = (1.32, 0.72, zc)
    perfil = [(0.17 + 0.016 * cos(2 * pi * k / 10), 0.016 * sin(2 * pi * k / 10)) for k in range(10)]
    vs, fs = revolucion(perfil, (0, 0, 0), n=40)
    rot = mathutils.Matrix.Rotation(math.radians(90), 4, "Y") @ mathutils.Matrix.Rotation(math.radians(-25), 4, "Z")
    vs = [tuple(Vector(cw) + (rot.to_3x3() @ Vector(v))) for v in vs]
    objeto("Volante", vs, fs, MAT["interior"])
    vs, fs = tubo([(1.18, 0.66, zc), (1.31, 0.715, zc)], 0.02)
    objeto("Columna", vs, fs, MAT["interior"])
    # pilotos de 1.75 m (maniquí validado en carroceria.py: cabeza 44 mm bajo el arco)
    for lado in (1, -1):
        z = lado * 0.31
        for a, b, r in (((1.900, 0.345), (2.005, 0.742), 0.10), ((1.900, 0.345), (1.560, 0.402), 0.07),
                        ((1.560, 0.402), (1.312, 0.268), 0.055), ((1.312, 0.268), (1.232, 0.238), 0.04)):
            vs, fs = tubo([(a[0], a[1], z), (b[0], b[1], z)], r, n=14)
            objeto("Piloto", vs, fs, MAT["piloto"])
        vs, fs = esfera((1.958, 0.862, z), 0.104)
        objeto("Cabeza", vs, fs, MAT["piloto"])


# ============================================================================
# 6. Escena, cámaras y render (misma convención que fotos.py)
# ============================================================================
ARRIBA = Vector((0.0, 1.0, 0.0))


def ejes_cam(pos, objetivo):
    z = (Vector(pos) - Vector(objetivo)).normalized()
    y = (ARRIBA - z * ARRIBA.dot(z))
    if y.length < 1e-6:
        y = Vector((-1.0, 0.0, 0.0))
    y.normalize()
    return y.cross(z), y, z


def mirar(pos, objetivo):
    x, y, z = ejes_cam(pos, objetivo)
    return mathutils.Matrix(((x.x, y.x, z.x), (x.y, y.y, z.y), (x.z, y.z, z.z))).to_euler()


def encuadre(caja_pts, pos, objetivo, aspecto, holgura):
    x, y, _ = ejes_cam(pos, objetivo)
    o = Vector(objetivo)
    us = [(Vector(p) - o).dot(x) for p in caja_pts]
    vs = [(Vector(p) - o).dot(y) for p in caja_pts]
    ancho = 2 * max(abs(min(us)), abs(max(us)))
    alto = 2 * max(abs(min(vs)), abs(max(vs)))
    return max(ancho, alto * aspecto) * holgura


def luz_area(pos, objetivo, sx, sy, pot):
    d = bpy.data.lights.new("l", "AREA")
    d.shape = "RECTANGLE"
    d.size, d.size_y, d.energy = sx, sy, pot
    o = bpy.data.objects.new("l", d)
    COL.objects.link(o)
    o.location = pos
    o.rotation_euler = mirar(pos, objetivo)


VISTAS = {
    "frontal": ((-1.0, 0.0, 0.0), 1.10, True),
    "trasera": ((1.0, 0.0, 0.0), 1.10, True),
    "lateral": ((0.0, 0.0, 1.0), 1.06, True),
    "cenital": ((0.0, 1.0, 0.02), 1.06, True),
    "tres_cuartos": ((-0.70, 0.36, 0.61), 1.08, False),
    "tres_cuartos_tras": ((0.72, 0.30, -0.62), 1.08, False),
}
# (posición de cámara, objetivo, lente mm) en coordenadas del proyecto
DETALLES = {
    "detalle_frente": ((-2.3, 0.75, 1.9), (0.25, 0.38, 0.15), 50),
    "detalle_cola": ((5.4, 0.85, -1.7), (3.05, 0.42, -0.1), 50),
}


def escena_y_render():
    L, H, W = X_COLA - X_MORRO, ALTO, 2 * SEMI
    foco = Vector((X_MORRO + L / 2, H * 0.42, 0.0))
    # piso
    vs = [(-30, 0, -30), (30, 0, -30), (30, 0, 30), (-30, 0, 30)]
    objeto("Piso", vs, [(0, 1, 2, 3)], MAT["piso"], suave=False, modelo=False)
    w = bpy.data.worlds.new("W")
    ESCENA.world = w
    w.use_nodes = True
    nt = w.node_tree
    fondo = nt.nodes["Background"]
    # degradado de estudio: claro arriba, gris al horizonte. Una pintura oscura con
    # clearcoat sólo se lee si tiene algo que reflejar.
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "LINEAR"
    mapa = nt.nodes.new("ShaderNodeMapping")
    mapa.inputs["Rotation"].default_value = (0.0, 0.0, 0.0)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    rampa.color_ramp.elements[0].position = 0.45
    rampa.color_ramp.elements[0].color = (0.24, 0.25, 0.28, 1)
    rampa.color_ramp.elements[1].position = 0.9
    rampa.color_ramp.elements[1].color = (0.60, 0.62, 0.66, 1)
    nt.links.new(coord.outputs["Generated"], sep.inputs["Vector"])
    # en la convención del proyecto la vertical es Y
    nt.links.new(sep.outputs["Y"], rampa.inputs["Fac"])
    nt.links.new(rampa.outputs["Color"], fondo.inputs["Color"])
    fondo.inputs["Strength"].default_value = 1.0
    bpy.data.materials["piso"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.78, 0.79, 0.81, 1)
    bpy.data.materials["piso"].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6
    luz_area((foco.x, 4.2, -1.2), foco, 7, 2.6, 480)          # softbox clave
    luz_area((foco.x + 0.5, 3.0, 3.4), foco, 5, 2.2, 240)     # relleno
    luz_area((X_MORRO - 3.0, 1.6, 1.6), (0.3, H * 0.4, 0), 3, 2, 200)   # recorte morro
    luz_area((X_COLA + 3.0, 1.6, -1.8), (X_COLA - 0.3, H * 0.4, 0), 3, 2, 200)

    e = ESCENA
    if RAPIDO:
        try:
            e.render.engine = "BLENDER_EEVEE_NEXT"
        except TypeError:
            e.render.engine = "BLENDER_EEVEE"
        e.eevee.taa_render_samples = 16
        pass
    else:
        e.render.engine = "CYCLES"
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "OPTIX"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == "OPTIX"
        e.cycles.device = "GPU"
        e.cycles.samples = int(arg("--muestras", "96"))
        e.cycles.use_denoising = True
    e.view_settings.view_transform = "AgX"
    e.view_settings.look = "AgX - Medium High Contrast"
    e.render.resolution_x = 1400
    e.render.resolution_y = 880
    esquinas = [(ex, ey, ez) for ex in (X_MORRO, X_COLA) for ey in (0.0, H) for ez in (-W / 2, W / 2)]
    aspecto = e.render.resolution_x / e.render.resolution_y
    piso = bpy.data.objects["Piso"]
    for nom, (dirn, holgura, orto) in VISTAS.items():
        if SOLO_VISTAS and nom not in SOLO_VISTAS:
            continue
        cd = bpy.data.cameras.new("c")
        c = bpy.data.objects.new("c", cd)
        COL.objects.link(c)
        if orto:
            cd.type = "ORTHO"
            c.location = foco + Vector(dirn).normalized() * 16
            cd.ortho_scale = encuadre(esquinas, c.location, foco, aspecto, holgura)
            e.render.film_transparent = True
            piso.hide_render = True
        else:
            cd.type = "PERSP"
            cd.lens = 42
            c.location = foco + Vector(dirn).normalized() * 6.3
            e.render.film_transparent = False
            piso.hide_render = False
        c.rotation_euler = mirar(c.location, foco)
        e.camera = c
        e.render.filepath = os.path.join(SAL, nom + ".png")
        bpy.ops.render.render(write_still=True)
        print("FOTO " + nom)
    # acercamientos para revisar detalle (no entran a la comparación de siluetas)
    e.render.film_transparent = False
    piso.hide_render = False
    for nom, (pos, objetivo, lente) in DETALLES.items():
        if SOLO_VISTAS and nom not in SOLO_VISTAS:
            continue
        cd = bpy.data.cameras.new("c")
        c = bpy.data.objects.new("c", cd)
        COL.objects.link(c)
        cd.lens = lente
        c.location = pos
        c.rotation_euler = mirar(pos, objetivo)
        e.camera = c
        e.render.filepath = os.path.join(SAL, nom + ".png")
        bpy.ops.render.render(write_still=True)
        print("FOTO " + nom)


# ============================================================================
# 7. Exportar
# ============================================================================
def exportar(cuerpo):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in MODELO:
        o.select_set(True)
    bpy.context.view_layer.objects.active = cuerpo
    bpy.ops.export_scene.gltf(filepath=os.path.join(CAD, "carro-v3.glb"), export_format="GLB",
                              use_selection=True, export_apply=True, export_yup=False,
                              export_materials="EXPORT")
    print("OK  cad/carro-v3.glb")
    activar(cuerpo)
    bpy.ops.wm.stl_export(filepath=os.path.join(CAD, "carro-v3-carroceria-mm.stl"),
                          export_selected_objects=True, global_scale=1000.0)
    print("OK  cad/carro-v3-carroceria-mm.stl")


# ============================================================================
# 8. MAQUETA IMPRIMIBLE (--maqueta N  ->  escala 1:N)
# ============================================================================
# Medidas en mm A ESCALA (lo que mide la pieza impresa). La junta y el cristal se
# exageran a propósito: una junta real de 6 mm a 1:16 mide 0.4 mm y una boquilla de
# 0.4 la borra (revisión de impresión, 2026-10-09).
JUNTA_MM = (0.8, 0.5)          # ancho, hondo de la junta de puerta
CRISTAL_MM = (0.5, 0.4)        # surco perimetral del cristal (guía para enmascarar)
ALETA_MIN_MM = 1.2             # 3 líneas de extrusión
EJE_MM = 2.1                   # agujero del eje (filamento 1.75), en gota


def _cadenas(aristas):
    """Encadena aristas (pares de índices) en polilíneas: [(índices, cerrada)]."""
    ady = {}
    for a, b in aristas:
        ady.setdefault(a, []).append(b)
        ady.setdefault(b, []).append(a)

    def clave(a, b):
        return (min(a, b), max(a, b))

    usadas, cadenas = set(), []
    inicios = [v for v, l in ady.items() if len(l) != 2] + list(ady)
    for v0 in inicios:
        for v1 in ady[v0]:
            if clave(v0, v1) in usadas:
                continue
            cad = [v0, v1]
            usadas.add(clave(v0, v1))
            while True:
                u = cad[-1]
                sig = [w for w in ady[u] if clave(u, w) not in usadas]
                if len(ady[u]) != 2 or not sig:
                    break
                usadas.add(clave(u, sig[0]))
                cad.append(sig[0])
            cerrada = cad[0] == cad[-1]
            cadenas.append((cad[:-1] if cerrada else cad, cerrada))
    return cadenas


def _suavizar_sobre_piel(cuerpo, pts, cerrada, veces=6):
    """Promedia la polilínea (quita los escalones de la subdivisión) y la vuelve a
    asentar sobre la piel."""
    for _ in range(veces):
        n = len(pts)
        if cerrada:
            pts = [(pts[k - 1] + 2 * pts[k] + pts[(k + 1) % n]) / 4 for k in range(n)]
        else:
            pts = [pts[0]] + [(pts[k - 1] + 2 * pts[k] + pts[k + 1]) / 4
                              for k in range(1, n - 1)] + [pts[-1]]
    P, N = [], []
    for p in pts:
        ok, loc, nor, _ = cuerpo.closest_point_on_mesh(p)
        if ok:
            P.append(loc)
            N.append(nor.normalized())
    return P, N


def surcos_de_cristal(cuerpo, ancho, hondo):
    """Surco en la orilla de cada cristal: las aristas entre caras de vidrio y el resto."""
    mats = [m.name if m else "" for m in cuerpo.data.materials]
    bm = bmesh.new()
    bm.from_mesh(cuerpo.data)

    def es_vidrio(f):
        return mats[f.material_index].startswith("vidrio")

    aristas = [(e.verts[0].index, e.verts[1].index) for e in bm.edges
               if len(e.link_faces) == 2
               and es_vidrio(e.link_faces[0]) != es_vidrio(e.link_faces[1])]
    co = [v.co.copy() for v in bm.verts]
    bm.free()
    hechas = 0
    for cad, cerrada in _cadenas(aristas):
        pts = [co[i] for i in cad]
        largo = sum((pts[k + 1] - pts[k]).length for k in range(len(pts) - 1))
        if largo < 0.15 or len(pts) < 6:
            continue
        P, N = _suavizar_sobre_piel(cuerpo, pts, cerrada)
        ranura_3d(cuerpo, P, N, ancho, hondo, "negro", cerrada)
        hechas += 1
    print(f"  maqueta: {hechas} surcos de cristal")


def surcos_de_puerta(cuerpo, ancho, hondo):
    """Las mismas juntas que juntas_de_puerta(), pero grabadas en la piel."""
    lado_xy = [(1.06, 0.30), (1.08, 0.40), (1.13, 0.52), (1.21, 0.66), (1.31, 0.80),
               (1.43, 0.92), (1.56, 0.99)]
    tras_xy = [(2.12, 0.99), (2.16, 0.90), (2.19, 0.76), (2.19, 0.60), (2.16, 0.45),
               (2.14, 0.30), (1.06, 0.30)]
    techo_xz = [(1.50, 0.50), (1.55, 0.40), (1.60, 0.28), (1.66, 0.18), (1.72, 0.15),
                (1.98, 0.15), (2.04, 0.18), (2.10, 0.28), (2.15, 0.40), (2.19, 0.50)]
    for lado in (1, -1):
        for linea in (lado_xy, tras_xy):
            P, N = [], []
            for (x, y) in _densificar(linea, 0.01):
                pos, nor = rayo(cuerpo, (x, y, lado * 2.0), (0, 0, -lado))
                if pos is not None:
                    P.append(pos)
                    N.append(nor if nor.z * lado > 0 else -nor)
            if len(P) > 3:
                ranura_3d(cuerpo, P, N, ancho, hondo, "negro")
        P, N = [], []
        for (x, z) in _densificar(techo_xz, 0.01):
            pos, nor = rayo(cuerpo, (x, 2.0, lado * z), (0, -1, 0))
            if pos is not None:
                P.append(pos)
                N.append(nor if nor.y > 0 else -nor)
        if len(P) > 3:
            ranura_3d(cuerpo, P, N, ancho, hondo, "negro")


def agujeros_de_eje(cuerpo, d):
    """Agujero pasante en z en cada eje, en GOTA (punta arriba): impreso acostado, el
    techo de un agujero redondo horizontal se cuelga; con punta a 45° no."""
    r = d / 2
    perfil = [(r * cos(math.radians(a)), r * sin(math.radians(a))) for a in range(-225, 46, 15)]
    perfil.append((0.0, r * math.sqrt(2)))
    m = len(perfil)
    for w in J["ruedas"][::2]:
        vs = []
        for z in (-1.2, 1.2):
            vs += [(w["x"] + u, w["R"] + v, z) for (u, v) in perfil]
        fs = [(k, (k + 1) % m, m + (k + 1) % m, m + k) for k in range(m)]
        fs += [tuple(range(m))[::-1], tuple(range(m, 2 * m))]
        ob = objeto("_eje", vs, fs, MAT["pozo"], modelo=False)
        normales(ob)
        CORTADORES.append(ob)


CORTADORES = None


def _stl(ob, ruta):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    activar(ob)
    bpy.ops.wm.stl_export(filepath=ruta, export_selected_objects=True, global_scale=1000.0)


def maqueta(cuerpo, escala):
    """Piezas de la maqueta a 1:escala para calculos/maqueta.py: la piel, lo que se le
    SUMA (splitter, aletas del difusor engrosadas) y lo que se le RESTA (juntas de
    puerta, orilla de cristales, agujeros de eje), cada una en su STL en mm reales.
    Los booleanos los hace manifold3d: el solver exacto de Blender, sobre la piel ya
    cortada, dejaba aristas abiertas y en una unión hasta BAJABA el volumen."""
    global CORTADORES
    mm = escala / 1000.0                      # 1 mm a escala, en metros reales
    d = os.path.join(CAD, f"_maqueta-1a{escala}")
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    _stl(cuerpo, os.path.join(d, "piel.stl"))
    sumar = [o for o in MODELO if o.name.startswith("Splitter")]
    sumar += difusor(cuerpo, espesor=max(0.014, ALETA_MIN_MM * mm), modelo=False)
    for i, o in enumerate(sumar):
        _stl(o, os.path.join(d, f"sumar-{i:02d}.stl"))
        if o not in MODELO:                   # las aletas engrosadas no se quedan en la escena
            borrar(o)
    CORTADORES = []
    surcos_de_puerta(cuerpo, JUNTA_MM[0] * mm, JUNTA_MM[1] * mm)
    surcos_de_cristal(cuerpo, CRISTAL_MM[0] * mm, CRISTAL_MM[1] * mm)
    agujeros_de_eje(cuerpo, EJE_MM * mm)
    for i, o in enumerate(CORTADORES):
        _stl(o, os.path.join(d, f"restar-{o.name.split('.')[0].strip('_')}-{i:02d}.stl"))
        borrar(o)
    CORTADORES = None
    json.dump({"escala": escala, "ruedas": J["ruedas"], "y_piso": Y_PISO,
               "eje_mm": EJE_MM, "z_pozo": 0.615},
              open(os.path.join(d, "datos.json"), "w", encoding="utf-8"), indent=1)
    print(f"OK  {d}: piel + {len(sumar)} para sumar + {len(os.listdir(d)) - 2 - len(sumar)} para restar")


def main():
    global CUERPO
    cuerpo = carroceria()
    CUERPO = cuerpo
    pasos_de_rueda(cuerpo)
    branquias(cuerpo)
    boca_parrilla(cuerpo)
    boca_difusor(cuerpo)
    luces(cuerpo)
    limpiar(cuerpo)
    tapar_agujeros(cuerpo)
    suavizar_por_angulo(cuerpo, 40)
    juntas_de_puerta(cuerpo)
    malla_parrilla(cuerpo)
    splitter(cuerpo)
    difusor(cuerpo)
    espejos(cuerpo)
    ruedas()
    interior()
    for o in MODELO:
        if o is not cuerpo and o.data.polygons and o.data.polygons[0].use_smooth:
            suavizar_por_angulo(o, 35)
    V = [v.co for v in cuerpo.data.vertices]
    print(f"MODELO  largo {max(v.x for v in V)-min(v.x for v in V):.3f}  ancho "
          f"{2*max(v.z for v in V):.3f}  alto {max(v.y for v in V):.3f}  "
          f"piezas {len(MODELO)}")
    if "--sin-exportar" not in ARGS:
        exportar(cuerpo)
    for esc in [int(e) for e in (arg("--maqueta") or "").split(",") if e]:
        maqueta(cuerpo, esc)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(CAD, "carro-v3.blend"))
    print("OK  cad/carro-v3.blend")
    if "--sin-render" not in ARGS:
        escena_y_render()


main()
