# -*- coding: utf-8 -*-
"""Abre en Blender (con ventana) el GLB de Tripo con su textura, a tres cuartos.

    blender --python render/abrir_tripo.py -- ref/tripo/tripo-multivista-h31.glb
"""
import math
import os
import sys

import bpy
from mathutils import Euler

GLB = os.path.abspath(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else \
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "ref", "tripo", "tripo-multivista-h31.glb")
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.import_scene.gltf(filepath=GLB)


def vista():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type != "VIEW_3D":
                continue
            for sp in area.spaces:
                if sp.type == "VIEW_3D":
                    sp.shading.type = "MATERIAL"
                    sp.clip_start, sp.clip_end = 0.001, 100
                    r3 = sp.region_3d
                    r3.view_perspective = "PERSP"
                    r3.view_location = (0.0, 0.0, 0.12)
                    r3.view_distance = 1.6
                    r3.view_rotation = Euler((math.radians(65), 0, math.radians(-140))).to_quaternion()
            area.tag_redraw()
    return None


bpy.app.timers.register(vista, first_interval=1.0)
