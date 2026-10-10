# -*- coding: utf-8 -*-
"""Abre en Blender (con ventana) el modelo completo y la maqueta imprimible lado a lado.

    blender cad/carro-v3.blend --python render/abrir_en_blender.py

La escena del proyecto usa Y-arriba; Blender usa Z-arriba. Aquí todo se cuelga de un
vacío girado 90° en X para que el carro quede parado sobre el piso. La maqueta 1:16 se
escala x16 y se pone a un lado, para compararla con el modelo a su mismo tamaño.
"""
import math
import os

import bpy

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STL = os.path.join(RAIZ, "impresion", "maqueta-1a16-carroceria.stl")

raiz = bpy.data.objects.new("Carro (Y-arriba -> Z-arriba)", None)
bpy.context.collection.objects.link(raiz)
raiz.rotation_euler = (math.radians(90), 0, 0)
raiz.empty_display_size = 0.05
for ob in list(bpy.context.scene.objects):
    if ob is not raiz and ob.parent is None:
        ob.parent = raiz

if os.path.exists(STL):
    bpy.ops.wm.stl_import(filepath=STL)
    maq = bpy.context.selected_objects[0]
    maq.name = "Maqueta 1:16 impresa (x16)"
    # el STL viene en mm a escala; Blender lo lee como metros: x16 / 1000
    maq.scale = (0.016, 0.016, 0.016)
    # el STL viene acostado para la cama (Z arriba, centrado): se pone en fila, delante del carro
    maq.location = (5.4, 0.0, 0.125)
    m = bpy.data.materials.new("PLA gris")
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.35, 0.36, 0.38, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.55
    maq.data.materials.append(m)
    bpy.ops.object.shade_auto_smooth(angle=math.radians(30))


def preparar_vista():
    """Vista fija a tres cuartos sobre los dos carros (view_all se iba lejísimos al
    correr antes de que la ventana terminara de armarse)."""
    from mathutils import Euler
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type != "VIEW_3D":
                continue
            for sp in area.spaces:
                if sp.type != "VIEW_3D":
                    continue
                sp.shading.type = "MATERIAL"
                sp.clip_start, sp.clip_end = 0.01, 1000
                r3 = sp.region_3d
                r3.view_perspective = "PERSP"
                r3.view_location = (2.6, 0.0, 0.45)
                r3.view_distance = 10.5
                r3.view_rotation = Euler((math.radians(66), 0, math.radians(-32))).to_quaternion()
            area.tag_redraw()
    return None


bpy.app.timers.register(preparar_vista, first_interval=1.0)
