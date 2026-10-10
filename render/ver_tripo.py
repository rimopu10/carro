# -*- coding: utf-8 -*-
"""Renders del GLB de Tripo en las mismas vistas que la lámina (ortográficas, fondo
transparente) + dos tres cuartos, para compararlo contra la referencia.

    blender --background --python render/ver_tripo.py -- ref/tripo/tripo-multivista-h31.glb render/salida/tripo

Tripo entrega Z arriba, largo en Y, normalizado a ~1 m. La nariz se detecta sola: es
el extremo en Y con el morro más bajo (la cola es alta y recta).
"""
import math
import os
import sys

import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:]
GLB, SAL = os.path.abspath(ARGS[0]), os.path.abspath(ARGS[1])
MUESTRAS = int(ARGS[2]) if len(ARGS) > 2 else 64
os.makedirs(SAL, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
ob = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
bpy.context.view_layer.update()
V = [ob.matrix_world @ v.co for v in ob.data.vertices]
ymin, ymax = min(v.y for v in V), max(v.y for v in V)
L = ymax - ymin


def alto_extremo(lado):
    """Altura máxima de la piel en el 6 % extremo del largo."""
    if lado < 0:
        sel = [v.z for v in V if v.y < ymin + 0.06 * L]
    else:
        sel = [v.z for v in V if v.y > ymax - 0.06 * L]
    return max(sel)


NARIZ = -1 if alto_extremo(-1) < alto_extremo(+1) else +1
print(f"NARIZ hacia {'-Y' if NARIZ < 0 else '+Y'}  (alto extremos: -Y {alto_extremo(-1):.3f}, +Y {alto_extremo(1):.3f})")
c = Vector(((min(v.x for v in V) + max(v.x for v in V)) / 2, (ymin + ymax) / 2,
            max(v.z for v in V) * 0.45))
dims = ob.dimensions

e = bpy.context.scene
w = bpy.data.worlds.new("w")
e.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.75, 0.77, 0.8, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
for pos, pot in (((0.6, -0.4, 1.4), 120), ((-0.9, 0.6, 0.7), 60)):
    d = bpy.data.lights.new("l", "AREA"); d.size = 1.2; d.energy = pot
    o = bpy.data.objects.new("l", d); e.collection.objects.link(o); o.location = pos
    o.rotation_euler = (c - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
e.render.engine = "CYCLES"
e.cycles.samples = MUESTRAS
e.cycles.device = "GPU"
p = bpy.context.preferences.addons["cycles"].preferences
p.compute_device_type = "OPTIX"
p.get_devices()
for dv in p.devices:
    dv.use = dv.type == "OPTIX"
e.render.resolution_x, e.render.resolution_y = 1400, 880
e.view_settings.view_transform = "AgX"

n = NARIZ
VISTAS = {  # nombre: (dirección desde el centro hacia la cámara, ortográfica)
    "frontal": ((0, n, 0), True), "trasera": ((0, -n, 0), True),
    "lateral": ((1 if n < 0 else -1, 0, 0), True),     # nariz a la izquierda de la imagen
    "cenital": ((0, 0, 1), True),
    "tres_cuartos": ((0.62 * (-1 if n < 0 else 1), 0.62 * n, 0.42), False),
    "tres_cuartos_tras": ((-0.62 * (-1 if n < 0 else 1), -0.62 * n, 0.36), False),
}
for nom, (dirn, orto) in VISTAS.items():
    cd = bpy.data.cameras.new("c")
    cam = bpy.data.objects.new("c", cd)
    e.collection.objects.link(cam)
    dv = Vector(dirn).normalized()
    if orto:
        cd.type = "ORTHO"
        cam.location = c + dv * 5
        ancho = dims.y if abs(dv.x) > 0.5 or abs(dv.z) > 0.5 else dims.x
        cd.ortho_scale = max(dims.y, dims.x) * 1.08 if nom == "cenital" else ancho * 1.10
        e.render.film_transparent = True
    else:
        cd.lens = 45
        cam.location = c + dv * 2.0
        e.render.film_transparent = False
    up = "Y" if nom != "cenital" else "Y"
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", up).to_euler()
    if nom == "cenital":   # nariz a la izquierda de la imagen, como la lámina
        cam.rotation_euler = (0, 0, math.radians(-90 if n > 0 else 90))
    e.camera = cam
    e.render.filepath = os.path.join(SAL, nom + ".png")
    bpy.ops.render.render(write_still=True)
    print("FOTO", nom)
