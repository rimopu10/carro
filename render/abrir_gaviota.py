# -*- coding: utf-8 -*-
"""Escena armada del juguete con puertas de gaviota (calculos/tripo_gaviota.py): la
carrocería, las dos puertas en su bisagra (la izquierda abierta), las 4 ruedas en sus
ejes y los pasadores de filamento. Se abre con ventana:

    blender --python render/abrir_gaviota.py -- [cad/_gaviota-1a20] [--angulo 65]

Las piezas vienen en mm a escala con los ejes del proyecto (Y arriba); todo se cuelga
de un vacío girado 90° en X para que en Blender quede parado.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Euler

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
D = os.path.abspath(ARGS[0]) if ARGS and not ARGS[0].startswith("--") else os.path.join(RAIZ, "cad", "_gaviota-1a20")
ANG = float(ARGS[ARGS.index("--angulo") + 1]) if "--angulo" in ARGS else 65.0
dat = json.load(open(os.path.join(D, "datos.json"), encoding="utf-8"))
k = 1.0 / dat["escala"]

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
e = bpy.context.scene
e.unit_settings.system = "METRIC"
e.unit_settings.scale_length = 0.001
e.unit_settings.length_unit = "MILLIMETERS"

raiz = bpy.data.objects.new("Juguete gaviota 1:%d" % dat["escala"], None)
e.collection.objects.link(raiz)
raiz.rotation_euler = (math.radians(90), 0, 0)
raiz.empty_display_size = 2


def mat(nombre, rgb):
    m = bpy.data.materials.new(nombre)
    m.diffuse_color = (*rgb, 1)
    return m


PINTURA = mat("pintura", (0.40, 0.35, 0.32))
PUERTA = mat("puerta", (0.48, 0.42, 0.38))
LLANTA = mat("llanta", (0.07, 0.07, 0.08))
FILAMENTO = mat("filamento", (0.85, 0.75, 0.15))


def importar(nombre, material, padre):
    bpy.ops.wm.stl_import(filepath=os.path.join(D, nombre))
    ob = bpy.context.selected_objects[0]
    ob.name = nombre[:-4]
    ob.data.materials.append(material)
    ob.parent = padre
    bpy.ops.object.shade_auto_smooth(angle=math.radians(30))
    return ob


importar("carroceria.stl", PINTURA, raiz)
for i in range(4):
    importar(f"rueda-{i}.stl", LLANTA, raiz)

# puertas: cada una colgada de un vacío en su eje de bisagra, que es lo que se gira
yb, zb = dat["bisagra"]["y"] * k, dat["bisagra"]["z"] * k
for lado, nom in ((1, "puerta-der.stl"), (-1, "puerta-izq.stl")):
    piv = bpy.data.objects.new(f"bisagra {'der' if lado > 0 else 'izq'}", None)
    e.collection.objects.link(piv)
    piv.parent = raiz
    piv.location = (0, yb, lado * zb)
    piv.empty_display_type = "SINGLE_ARROW"
    ob = importar(nom, PUERTA, piv)
    ob.location = (0, -yb, -lado * zb)
    # gaviota: gira sobre x; la izquierda (z<0) sube con ángulo positivo, la derecha negativo
    if lado < 0:
        piv.rotation_euler = (math.radians(ANG), 0, 0)


def cilindro(nombre, r, largo, loc, rot, padre):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=largo, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = nombre
    ob.data.materials.append(FILAMENTO)
    ob.parent = padre
    return ob


for x in dat["ejes_x"]:
    cilindro("eje (filamento 1.75)", 0.875, 2 * dat["z_ext"] * k - 1, (x * k, dat["y_eje"] * k, 0),
             (0, 0, 0), raiz)
x0, x1 = dat["bisagra"]["x"]
for lado in (1, -1):
    cilindro("pasador de bisagra", 0.875, (x1 - x0) * k - 2, ((x0 + x1) / 2 * k, yb, lado * zb),
             (0, math.radians(90), 0), raiz)


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
                sp.shading.show_shadows = True
                sp.clip_start, sp.clip_end = 0.5, 5000
                r3 = sp.region_3d
                r3.view_perspective = "PERSP"
                r3.view_location = (85, 0, 25)
                r3.view_distance = 300
                # tres cuartos desde adelante a la izquierda, para ver la puerta abierta
                r3.view_rotation = Euler((math.radians(65), 0, math.radians(-150))).to_quaternion()
            area.tag_redraw()
    return None


bpy.app.timers.register(vista, first_interval=1.0)
