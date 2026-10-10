# -*- coding: utf-8 -*-
"""Abre un STL de impresion/ en Blender (con ventana), en milímetros y sobre la cama
de la Ender 3 V3 SE (220 x 220) para ver cómo queda y que cabe.

    blender --python render/abrir_stl.py -- impresion/juguete-tripo-1a20.stl
"""
import math
import os
import sys

import bpy
from mathutils import Euler

STL = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
CAMA = 220.0

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
e = bpy.context.scene
e.unit_settings.system = "METRIC"
e.unit_settings.scale_length = 0.001          # 1 unidad de Blender = 1 mm
e.unit_settings.length_unit = "MILLIMETERS"

bpy.ops.wm.stl_import(filepath=STL)
pieza = bpy.context.selected_objects[0]
bpy.ops.object.shade_auto_smooth(angle=math.radians(30))
m = bpy.data.materials.new("PLA")
m.diffuse_color = (0.55, 0.57, 0.6, 1)
pieza.data.materials.append(m)

# la cama: placa de 220 x 220 x 1 mm, centrada como la deja calculos/maqueta.py
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.5))
cama = bpy.context.active_object
cama.name = "Cama Ender 3 V3 SE 220x220"
cama.scale = (CAMA, CAMA, 1)
mc = bpy.data.materials.new("cama")
mc.diffuse_color = (0.08, 0.08, 0.09, 1)
cama.data.materials.append(mc)
for o in bpy.context.view_layer.objects:
    o.select_set(o is pieza)
bpy.context.view_layer.objects.active = pieza


def vista():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type != "VIEW_3D":
                continue
            for sp in area.spaces:
                if sp.type != "VIEW_3D":
                    continue
                sp.shading.type = "SOLID"
                sp.shading.color_type = "MATERIAL"
                sp.shading.show_cavity = True
                sp.shading.cavity_type = "BOTH"
                sp.shading.show_shadows = True
                sp.overlay.show_floor = False
                sp.clip_start, sp.clip_end = 0.5, 5000
                r3 = sp.region_3d
                r3.view_perspective = "PERSP"
                r3.view_location = (0, 0, 25)
                r3.view_distance = 330
                r3.view_rotation = Euler((math.radians(62), 0, math.radians(-35))).to_quaternion()
            area.tag_redraw()
    return None


bpy.app.timers.register(vista, first_interval=1.0)
