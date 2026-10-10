# -*- coding: utf-8 -*-
"""
Enseña la malla que generó la IA, tal cual salió y sin maquillaje.

El objetivo de este script NO es que se vea bonita: es poder juzgar si la forma sirve
antes de invertir trabajo en reorientarla al chasis. Por eso va en arcilla mate, con
la misma luz de estudio, y con una regla: se dibuja la caja de dimensiones y las
proporciones medidas, para compararlas contra la referencia.

    blender --background --python render/ver_malla_ia.py -- --glb cad/referencia-ia.glb
"""
import os
import sys

import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(n, d):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "render", "salida")
os.makedirs(SALIDA, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
glb = os.path.join(RAIZ, arg("--glb", "cad/referencia-ia.glb"))
if not os.path.exists(glb):
    raise SystemExit(f"no existe {glb}")
bpy.ops.import_scene.gltf(filepath=glb)

mallas = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if not mallas:
    raise SystemExit("el archivo no traia mallas")
for o in mallas:
    o.select_set(True)
bpy.context.view_layer.objects.active = mallas[0]
if len(mallas) > 1:
    bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
ob.name = "MallaIA"

# El modelo entrega en caja unitaria, con orientacion arbitraria y con una PLACA de
# apoyo debajo (estos modelos casi siempre inventan un pedestal). Hay que quitar la
# placa y alinear los ejes antes de poder juzgar nada.
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.select_all(action='DESELECT')
ob.select_set(True)
bpy.context.view_layer.objects.active = ob
import math                                                         # noqa: E402
import bmesh                                                        # noqa: E402
import mathutils                                                    # noqa: E402


def caja(o):
    """Caja leída de los VÉRTICES, no de ob.bound_box: ese queda cacheado después de
    transformar la malla y devuelve las cotas viejas."""
    vs = [v.co for v in o.data.vertices]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return mn, mx, mx - mn


mn, mx, d = caja(ob)
print(f"DIM_IMPORTADA  x={d.x:.3f} y={d.y:.3f} z={d.z:.3f}")

# alinear: el eje más largo pasa a ser X. Se usa una ROTACIÓN, no un intercambio de
# ejes: intercambiar dos ejes tiene determinante -1 y espeja la pieza.
if d.y > d.x:
    ob.data.transform(mathutils.Matrix.Rotation(math.radians(-90), 4, 'Z'))
    ob.data.update()
    mn, mx, d = caja(ob)
if d.z > d.y:                       # el alto tiene que ser el eje corto
    ob.data.transform(mathutils.Matrix.Rotation(math.radians(90), 4, 'X'))
    ob.data.update()
    mn, mx, d = caja(ob)
print(f"ALINEADA       x={d.x:.3f} y={d.y:.3f} z={d.z:.3f}")

# quitar el pedestal: el modelo fusiona una placa de apoyo al cuerpo, así que no se
# puede separar como pieza suelta — se corta con un plano y se borra lo de abajo
corte = mn.z + d.z * 0.030
bm = bmesh.new()
bm.from_mesh(ob.data)
res = bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                             plane_co=(0, 0, corte), plane_no=(0, 0, 1), clear_inner=True)
bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary])
bm.to_mesh(ob.data)
bm.free()
ob.data.update()
mn, mx, d = caja(ob)
print(f"SIN_PEDESTAL   x={d.x:.3f} y={d.y:.3f} z={d.z:.3f}  caras={len(ob.data.polygons)}")


def recortar_apendices(o, salto=0.06):
    """Corta los CARTELES que el generador pega en los extremos.

    Fallo típico de la reconstrucción multivista: interpreta la vista frontal o la
    trasera como un panel plano y lo deja parado contra el carro. Medir el ancho no
    sirve — el cartel es tan ancho como el carro. Lo que sí lo delata es el PERFIL:
    pasado el techo, la carrocería sólo puede bajar; si la altura vuelve a subir, eso
    ya no es carro. Se corta ahí, por los dos extremos.
    """
    import numpy as np
    vs = np.array([[v.co.x, v.co.y, v.co.z] for v in o.data.vertices])
    n = 160
    xs = np.linspace(vs[:, 0].min(), vs[:, 0].max(), n)
    alto = np.zeros(n - 1)
    for i in range(n - 1):
        sel = vs[(vs[:, 0] >= xs[i]) & (vs[:, 0] < xs[i + 1])]
        alto[i] = sel[:, 2].max() if len(sel) > 3 else 0.0
    H = alto.max()
    total = vs[:, 0].max() - vs[:, 0].min()
    # Un cartel plano produce un ESCALÓN casi vertical en el perfil de alturas. Buscar
    # "el pico del techo" no sirve: el cartel suele ser más alto que el techo y el pico
    # cae sobre él. Se buscan saltos bruscos, y sólo en los extremos de la pieza.
    d = np.diff(alto)
    umbral = 0.12 * H
    borde = int(n * 0.22)
    x_ini, x_fin = vs[:, 0].min(), vs[:, 0].max()
    caidas = [i for i in range(borde) if d[i] < -umbral]        # cartel delantero
    if caidas:
        x_ini = xs[max(caidas) + 1]
    subidas = [i for i in range(n - 1 - borde, n - 2) if d[i] > umbral]   # cartel trasero
    if subidas:
        x_fin = xs[min(subidas)]
    if (x_fin - x_ini) < 0.60 * total:      # recorte absurdo: mejor no tocar nada
        print(f"APENDICES      descartado (recorte de {(x_fin-x_ini)/total:.0%})")
        return

    if (x_ini - vs[:, 0].min()) < 0.004 * total and (vs[:, 0].max() - x_fin) < 0.004 * total:
        print("APENDICES      ninguno")
        return
    print(f"APENDICES      cartel detectado · se recorta a x=[{x_ini:.3f}, {x_fin:.3f}] "
          f"de [{vs[:, 0].min():.3f}, {vs[:, 0].max():.3f}]")
    bm2 = bmesh.new()
    bm2.from_mesh(o.data)
    for co, no in (((x_ini, 0, 0), (-1, 0, 0)), ((x_fin, 0, 0), (1, 0, 0))):
        bmesh.ops.bisect_plane(bm2, geom=list(bm2.verts) + list(bm2.edges) + list(bm2.faces),
                               plane_co=co, plane_no=no, clear_outer=True)
    r = bmesh.ops.holes_fill(bm2, edges=[e for e in bm2.edges if e.is_boundary])
    # holes_fill tapa el hueco con UNA sola cara enorme. Como el material se asigna por
    # cara, esa cara única se pintaba entera del color de la luz. Hay que trocearla.
    tapas = [f for f in r.get("faces", []) if f.is_valid]
    if tapas:
        pk = bmesh.ops.poke(bm2, faces=tapas)
        aristas = {e for f in pk["faces"] if f.is_valid for e in f.edges}
        bmesh.ops.subdivide_edges(bm2, edges=list(aristas), cuts=10, use_grid_fill=True)
        print(f"TAPA_COLA      {len(tapas)} cara(s) troceadas")
    bm2.to_mesh(o.data)
    bm2.free()
    o.data.update()


if arg("--recorte", "1") == "1":
    recortar_apendices(ob)
mn, mx, d = caja(ob)
print(f"LIMPIA         x={d.x:.3f} y={d.y:.3f} z={d.z:.3f}  caras={len(ob.data.polygons)}")
dim = d
print(f"DIM_CRUDA  x={dim.x:.3f} y={dim.y:.3f} z={dim.z:.3f}")
print(f"CARAS      {len(ob.data.polygons)}   VERTICES {len(ob.data.vertices)}")

# el eje mas largo es el LARGO del carro; el mas corto de los otros dos, el ALTO
ejes = sorted([(dim.x, 'X'), (dim.y, 'Y'), (dim.z, 'Z')], reverse=True)
print(f"PROPORCIONES  largo/alto={ejes[0][0]/ejes[2][0]:.2f}  "
      f"ancho/alto={ejes[1][0]/ejes[2][0]:.2f}   (referencia: 3.5 y 1.7 aprox)")

# escalar a 3.35 m de largo y apoyar en el piso, sin deformar
esc = 3.35 / ejes[0][0]
ob.scale = (esc, esc, esc)
bpy.ops.object.transform_apply(scale=True)
bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
mn = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
mx = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
ob.location -= Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
bpy.ops.object.transform_apply(location=True)
for p in ob.data.polygons:
    p.use_smooth = True

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
    sal = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs["Emission"], sal.inputs["Surface"])
    return m


ARCILLA = arg("--arcilla", "0") == "1"
if ARCILLA:
    MATS = [princ("Arcilla", **{"Base Color": (0.52, 0.53, 0.56, 1),
                                "Roughness": 0.48, "Metallic": 0.0})] * 5
else:
    MATS = [
        # Color MEDIDO de la referencia del dueño (sRGB 115,106,102 -> lineal).
        # Antes iba casi negro con capa transparente al máximo: sobre fondo oscuro los
        # reflejos se revientan y la carrocería parece tinta líquida, no pintura.
        # Metalizado BAJO. Una pintura automotriz real refleja el entorno difuso, no
        # como un espejo: el efecto espejo viene de metallic alto + rugosidad baja.
        princ("Pintura", **{"Base Color": (0.173, 0.145, 0.133, 1), "Metallic": 0.22,
                            "Roughness": 0.38, "Coat Weight": 0.35,
                            "Coat Roughness": 0.16, "Specular IOR Level": 0.45}),
        princ("Vidrio", **{"Base Color": (0.06, 0.065, 0.075, 1), "Roughness": 0.05,
                           "Transmission Weight": 0.80, "IOR": 1.52}),
        princ("Negro", **{"Base Color": (0.016, 0.018, 0.021, 1), "Roughness": 0.42}),
        emisivo("LuzTrasera", (1.0, 0.06, 0.10), 2.2),
        emisivo("LuzDelantera", (0.70, 0.86, 1.0), 2.0),
    ]
ob.data.materials.clear()
for mm in MATS:
    ob.data.materials.append(mm)

# ¿de qué lado está el morro? El extremo del morro es más BAJO que el de la cola.
vs = [v.co for v in ob.data.vertices]
x0 = min(v.x for v in vs)
x1 = max(v.x for v in vs)
L = x1 - x0
z0 = min(v.z for v in vs)
H = max(v.z for v in vs) - z0
alt_ini = sum(v.z for v in vs if v.x < x0 + 0.10 * L) / max(1, sum(1 for v in vs if v.x < x0 + 0.10 * L))
alt_fin = sum(v.z for v in vs if v.x > x1 - 0.10 * L) / max(1, sum(1 for v in vs if v.x > x1 - 0.10 * L))
morro_en_x0 = alt_ini < alt_fin
print(f"MORRO   {'x minimo' if morro_en_x0 else 'x maximo'} "
      f"(alturas medias {alt_ini:.3f} vs {alt_fin:.3f})")

if not ARCILLA:
    for p in ob.data.polygons:
        c = p.center
        fx = (c.x - x0) / L
        if not morro_en_x0:
            fx = 1.0 - fx
        fz = (c.z - z0) / H
        # la normal decide si la cara MIRA hacia adelante o atras: sin esto la luz se
        # pinta sobre toda la trasera, que es una cara plana entera
        nx = p.normal.x * (1.0 if morro_en_x0 else -1.0)
        if fz < 0.135:
            p.material_index = 2                       # faldón / bajos
        elif fx > 0.955 and nx > 0.55 and 0.345 < fz < 0.425:
            p.material_index = 3                       # barra trasera
        elif fx < 0.045 and nx < -0.50 and 0.30 < fz < 0.375:
            p.material_index = 4                       # cejas delanteras
        elif 0.33 < fx < 0.79 and fz > 0.615 and p.normal.z > -0.25:
            p.material_index = 1                       # cristal de la cabina
        else:
            p.material_index = 0

# estudio
piso_m = bpy.data.materials.new("Piso")
piso_m.use_nodes = True
pb = piso_m.node_tree.nodes["Principled BSDF"]
CLARO = arg("--estudio", "claro") == "claro"
pb.inputs["Base Color"].default_value = ((0.62, 0.62, 0.63, 1) if CLARO
                                         else (0.06, 0.063, 0.07, 1))
pb.inputs["Roughness"].default_value = 0.42 if CLARO else 0.35
me = bpy.data.meshes.new("Piso")
me.from_pydata([(-14, -14, 0), (18, -14, 0), (18, 14, 0), (-14, 14, 0)], [], [(0, 1, 2, 3)])
piso = bpy.data.objects.new("Piso", me)
bpy.context.collection.objects.link(piso)
piso.data.materials.append(piso_m)

mundo = bpy.data.worlds.new("W")
bpy.context.scene.world = mundo
mundo.use_nodes = True
mundo.node_tree.nodes["Background"].inputs[0].default_value = (
    (0.72, 0.73, 0.75, 1) if CLARO else (0.021, 0.024, 0.030, 1))


def area(nombre, pos, mira, w, h, pot):
    d = bpy.data.lights.new(nombre, 'AREA')
    d.shape, d.size, d.size_y, d.energy = 'RECTANGLE', w, h, pot
    o = bpy.data.objects.new(nombre, d)
    bpy.context.collection.objects.link(o)
    o.location = pos
    o.rotation_euler = (Vector(mira) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()


if CLARO:
    # estudio de catálogo: luz envolvente y contraste bajo, como tus referencias
    area("franja", (0.0, -0.5, 4.6), (0, 0, 0.5), 9.0, 2.4, 700)
    area("clave", (3.4, -4.2, 3.0), (0, 0, 0.5), 4.0, 4.0, 420)
    area("relleno", (-3.0, 4.2, 2.6), (0, 0, 0.5), 5.0, 4.0, 340)
    area("lateral", (0.0, 5.5, 1.2), (0, 0, 0.5), 6.0, 2.0, 240)
else:
    area("franja", (0.0, -0.6, 4.2), (0, 0, 0.5), 7.0, 1.1, 900)
    area("clave", (3.6, -4.6, 3.2), (0, 0, 0.5), 3.2, 3.2, 700)
    area("relleno", (-2.6, 4.4, 2.4), (0, 0, 0.5), 4.0, 3.0, 260)

e = bpy.context.scene
e.render.engine = 'CYCLES'
e.cycles.device = 'CPU'
e.cycles.samples = int(arg("--muestras", "48"))
e.cycles.use_denoising = True
e.render.resolution_x, e.render.resolution_y = 1600, 900
e.view_settings.view_transform = 'AgX'

# El encuadre importa: con 80 mm a 6 m un carro de 3.35 m no cabe. Distancia
# calculada para que entre completo con aire alrededor.
VISTAS = {"34frente": ((-6.30, -6.40, 1.55), (0.05, 0, 0.44), 72),
          "lateral": ((0.0, -17.0, 0.62), (0.0, 0, 0.50), 105),
          "34atras": ((6.50, -6.20, 1.65), (-0.05, 0, 0.44), 72),
          "frontal": ((-15.0, 0.0, 0.62), (0.0, 0, 0.48), 105)}
for nom, (pos, mira, foc) in VISTAS.items():
    cd = bpy.data.cameras.new("c")
    cd.lens = foc
    c = bpy.data.objects.new("c", cd)
    bpy.context.collection.objects.link(c)
    c.location = pos
    c.rotation_euler = (Vector(mira) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    e.camera = c
    e.render.filepath = os.path.join(SALIDA, f"ia-{nom}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDER OK", e.render.filepath)
