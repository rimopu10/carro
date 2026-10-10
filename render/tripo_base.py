# -*- coding: utf-8 -*-
"""
Base común de la carrocería de Tripo: a escala real, en los ejes del proyecto y como
sólido cerrado. De aquí salen las tres versiones (juguete, RC y real).

    blender --background --python render/tripo_base.py -- [--voxel 0.004]

1. Importa ref/tripo/tripo-multivista-h31.glb y se queda con la pieza principal (Tripo
   deja ~116 fragmentos sueltos de pocas caras).
2. Ejes del proyecto: X largo con la nariz hacia -X, Y arriba, Z lateral. Escala por
   la BATALLA: los contactos de las llantas con el piso quedan a 2.130 m y el eje
   delantero en x = 0.55, como en el chasis. Así el carro de Tripo cae sobre los
   mismos puntos duros que el diseño actual.
3. cad/carroceria-tripo.glb: con su textura, para verla (no va en git, 60+ MB).
4. Sólido: la malla de Tripo trae 211 aristas abiertas y 189 compartidas por más de
   dos caras, así que ni manifold ni un slicer la toman. Se reconstruye por vóxeles
   (--voxel, en m reales; 4 mm = 0.25 mm a 1:16) y se reduce a ~1.2 M triángulos.
   -> cad/carroceria-tripo-solida-mm.stl  (mm reales, sin textura)
5. cad/carroceria-tripo.json: medidas (batalla, vía, ruedas, largo, alto, piso).
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(n, d):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAD = os.path.join(RAIZ, "cad")
GLB = os.path.join(RAIZ, "ref", "tripo", "tripo-multivista-h31.glb")
VOXEL = float(arg("--voxel", "0.004"))
TRIS = int(float(arg("--tris", "1.2e6")))
BATALLA, EJE_DEL = 2.130, 0.55

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
ob = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
ob.name = "CarroceriaTripo"
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# ---- 1. pieza principal --------------------------------------------------------------
bm = bmesh.new()
bm.from_mesh(ob.data)
# el glTF parte los vértices en las costuras de la textura: sin soldarlos, la malla se
# lee como ~2200 pedazos. Las UV van por esquina de cara, así que soldar no las pierde.
n_antes = len(bm.verts)
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
print(f"SOLDADO {n_antes} -> {len(bm.verts)} vértices")
bm.verts.ensure_lookup_table()
visto, grupos = set(), []
for v0 in bm.verts:
    if v0.index in visto:
        continue
    pila, g = [v0], []
    visto.add(v0.index)
    while pila:
        v = pila.pop()
        g.append(v)
        for e in v.link_edges:
            o = e.other_vert(v)
            if o.index not in visto:
                visto.add(o.index)
                pila.append(o)
    grupos.append(g)
grupos.sort(key=len, reverse=True)
basura = [v for g in grupos[1:] for v in g]
bmesh.ops.delete(bm, geom=basura, context="VERTS")
print(f"PIEZAS  {len(grupos)} -> 1 ({len(basura)} vértices sueltos fuera)")

# ---- 2. ejes y escala --------------------------------------------------------------
# Blender tras importar: x lateral, y largo (nariz en -y, ver render/ver_tripo.py), z arriba
co = [v.co.copy() for v in bm.verts]
suelo = [c for c in co if c.z < 0.004]
nariz = [c.y for c in suelo if c.y < 0]
cola = [c.y for c in suelo if c.y > 0]
y_del, y_tras = sum(nariz) / len(nariz), sum(cola) / len(cola)
k = BATALLA / (y_tras - y_del)
# proyecto = (x, y, z) <- (y_b, z_b, x_b): permutación cíclica, rotación propia
R = Matrix(((0, 1, 0), (0, 0, 1), (1, 0, 0))).to_4x4()
T = Matrix.Translation((EJE_DEL - y_del * k, 0, 0)) @ Matrix.Scale(k, 4) @ R
bm.transform(T)
bm.to_mesh(ob.data)
bm.free()
ob.data.update()
V = [v.co for v in ob.data.vertices]
lo = Vector([min(v[i] for v in V) for i in range(3)])
hi = Vector([max(v[i] for v in V) for i in range(3)])
print(f"ESCALA  x{k:.4f}  ->  largo {hi.x - lo.x:.3f}  alto {hi.y:.3f}  ancho {hi.z - lo.z:.3f} m")


def rueda(x_eje, lado):
    """Radio y ancho de la llanta por los vértices del costado dentro del pozo."""
    sel = [v for v in V if abs(v.x - x_eje) < 0.40 and v.z * lado > 0.55 and v.y < 0.75]
    r = max(math.hypot(v.x - x_eje, v.y - 0.0) for v in sel if v.y < 0.02) if sel else 0
    # el radio se mide del contacto al punto más alto de la llanta sobre el eje
    sobre = [v.y for v in sel if abs(v.x - x_eje) < 0.02 and v.z * lado > 0.66]
    alto = max(sobre) if sobre else 0
    zs = [abs(v.z) for v in sel if v.y < 0.05]
    return {"x": round(x_eje, 4), "lado": lado, "alto_llanta": round(alto, 4),
            "z_ext": round(max(zs), 4) if zs else None, "z_int": round(min(zs), 4) if zs else None}


medidas = {"escala": round(k, 5), "batalla": BATALLA,
           "largo": round(hi.x - lo.x, 4), "x_nariz": round(lo.x, 4), "x_cola": round(hi.x, 4),
           "ancho": round(hi.z - lo.z, 4), "alto": round(hi.y, 4),
           "ruedas": [rueda(EJE_DEL, 1), rueda(EJE_DEL + BATALLA, 1)]}

# ---- 3. versión con textura (para verla) --------------------------------------------
for o in bpy.context.view_layer.objects:
    o.select_set(o is ob)
bpy.ops.export_scene.gltf(filepath=os.path.join(CAD, "carroceria-tripo.glb"), export_format="GLB",
                          use_selection=True, export_yup=False)
print("OK  cad/carroceria-tripo.glb")

# ---- 4. sólido por vóxeles ------------------------------------------------------------
sol = ob.copy()
sol.data = ob.data.copy()
sol.name = "CarroceriaTripo_solida"
bpy.context.collection.objects.link(sol)
for o in bpy.context.view_layer.objects:
    o.select_set(o is sol)
bpy.context.view_layer.objects.active = sol
m = sol.modifiers.new("remesh", "REMESH")
m.mode = "VOXEL"
m.voxel_size = VOXEL
m.adaptivity = 0.0
m.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier=m.name)
n0 = len(sol.data.polygons)
bpy.ops.object.modifier_add(type="TRIANGULATE")
bpy.ops.object.modifier_apply(modifier="Triangulate")
n1 = len(sol.data.polygons)
if n1 > TRIS:
    d = sol.modifiers.new("dec", "DECIMATE")
    d.ratio = TRIS / n1
    bpy.ops.object.modifier_apply(modifier=d.name)
bm = bmesh.new()
bm.from_mesh(sol.data)
nm = sum(1 for e in bm.edges if not e.is_manifold)
vol = bm.calc_volume(signed=True)
bm.free()
print(f"SOLIDO  voxel {VOXEL*1000:.0f} mm: {n0} quads -> {len(sol.data.polygons)} triángulos, "
      f"{nm} aristas no manifold, volumen {vol:.3f} m3")
bpy.ops.wm.stl_export(filepath=os.path.join(CAD, "carroceria-tripo-solida-mm.stl"),
                      export_selected_objects=True, global_scale=1000.0)
print("OK  cad/carroceria-tripo-solida-mm.stl")
medidas["solido"] = {"voxel_m": VOXEL, "triangulos": len(sol.data.polygons),
                     "no_manifold": nm, "volumen_m3": round(vol, 4)}
json.dump(medidas, open(os.path.join(CAD, "carroceria-tripo.json"), "w", encoding="utf-8"), indent=1)
print("MEDIDAS", json.dumps(medidas))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(CAD, "carroceria-tripo.blend"))
