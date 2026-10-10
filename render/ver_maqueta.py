# -*- coding: utf-8 -*-
"""Vista previa de los STL de impresion/ como pieza de PLA gris (para revisar surcos,
detalle y que nada se haya roto en los booleanos antes de mandar a la impresora).

    blender --background --python render/ver_maqueta.py -- impresion/maqueta-1a16-carroceria.stl salida.png
"""
import math
import sys

import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:]
STL, PNG = ARGS[0], ARGS[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.stl_import(filepath=STL)
ob = bpy.context.selected_objects[0]
bpy.ops.object.shade_auto_smooth(angle=math.radians(30))
m = bpy.data.materials.new("pla")
m.use_nodes = True
b = m.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.32, 0.33, 0.35, 1)
b.inputs["Roughness"].default_value = 0.55
ob.data.materials.append(m)
dim = ob.dimensions
c = Vector([(a + b_) / 2 for a, b_ in zip([min(v.co[i] for v in ob.data.vertices) for i in range(3)],
                                       [max(v.co[i] for v in ob.data.vertices) for i in range(3)])])
e = bpy.context.scene
w = bpy.data.worlds.new("w"); e.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.57, 0.6, 1)
for pos, pot in (((c.x - 150, c.y + 200, c.z + 300), 1.2e6), ((c.x + 300, c.y - 250, c.z + 120), 5e5)):
    L = bpy.data.lights.new("l", "AREA"); L.size = 250; L.energy = pot
    o = bpy.data.objects.new("l", L); e.collection.objects.link(o); o.location = pos
    o.rotation_euler = (Vector(c) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
e.render.engine = "CYCLES"; e.cycles.samples = 48; e.cycles.device = "GPU"
p = bpy.context.preferences.addons["cycles"].preferences; p.compute_device_type = "OPTIX"; p.get_devices()
for d in p.devices: d.use = d.type == "OPTIX"
e.render.resolution_x, e.render.resolution_y = 1400, 880
e.view_settings.view_transform = "AgX"
# pieza acostada: x largo (nariz en -x), y lateral, z arriba
vistas = [("frente", (-1.0, -0.85, 0.65)), ("cola", (1.0, 0.85, 0.55)),
          ("lado", (0.0, -1.0, 0.12)), ("arriba", (0.02, 0.0, 1.0))]
for suf, dirn in vistas:
    cd = bpy.data.cameras.new("c"); cd.lens = 60
    cam = bpy.data.objects.new("c", cd); e.collection.objects.link(cam)
    cam.location = c + Vector(dirn).normalized() * max(dim) * 1.9
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    e.camera = cam
    e.render.filepath = PNG.replace(".png", f"-{suf}.png")
    bpy.ops.render.render(write_still=True)
