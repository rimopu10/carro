# -*- coding: utf-8 -*-
"""
Fotografia de estudio del modelo, en la convencion del proyecto (X largo, Y ALTO,
Z lateral).

Ese detalle no es menor: Blender asume mundo Z-arriba, y `to_track_quat('-Z','Y')`
alinea el eje vertical de la camara con la Z del mundo —que aqui es el eje lateral—.
Resultado: el carro sale acostado. La matriz de la camara se arma a mano contra la Y.

    blender --background --python render/fotos.py -- --blend cad/carro-luces.blend
"""
import math
import os
import sys

import bpy
import mathutils
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(n, d):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAL = os.path.join(RAIZ, "render", "salida", arg("--sal", "estudio"))
ARRIBA = Vector((0.0, 1.0, 0.0))

VISTAS = {                       # nombre: (direccion desde la que se mira, holgura)
    "frontal":           ((-1.00, 0.00, 0.00), 1.16),
    "trasera":           ((1.00, 0.00, 0.00), 1.16),
    "lateral":           ((0.00, 0.00, 1.00), 1.10),
    "tres_cuartos":      ((-0.72, 0.30, 0.62), 1.10),
    "tres_cuartos_tras": ((0.72, 0.28, 0.60), 1.10),
    "cenital":           ((0.00, 1.00, 0.02), 1.10),
}


def ejes(pos, objetivo):
    """Terna de la camara con la Y del mundo como vertical."""
    z = (Vector(pos) - Vector(objetivo)).normalized()      # +Z local mira hacia atras
    y = (ARRIBA - z * ARRIBA.dot(z))
    if y.length < 1e-6:                                    # cenital: la vertical se
        y = Vector((-1.0, 0.0, 0.0))                       # degenera, se fija a mano
    y.normalize()
    return y.cross(z), y, z


def mirar(pos, objetivo):
    x, y, z = ejes(pos, objetivo)
    return mathutils.Matrix(((x.x, y.x, z.x),
                             (x.y, y.y, z.y),
                             (x.z, y.z, z.z))).to_euler()


def encuadre(caja, pos, objetivo, aspecto, holgura):
    """Cuanto tiene que abarcar la camara ortografica para que quepa el carro.

    A ojo no funciona: la misma cifra encuadra bien el lateral y deja la frontal
    recortada, porque lo que hay que medir no es el largo del carro sino su sombra
    sobre el plano de la camara, que cambia en cada vista.
    """
    x, y, _ = ejes(pos, objetivo)
    o = Vector(objetivo)
    us = [(Vector(p) - o).dot(x) for p in caja]
    vs = [(Vector(p) - o).dot(y) for p in caja]
    ancho = 2 * max(abs(min(us)), abs(max(us)))
    alto = 2 * max(abs(min(vs)), abs(max(vs)))
    return max(ancho, alto * aspecto) * holgura


def area(pos, objetivo, sx, sy, pot):
    d = bpy.data.lights.new("l", 'AREA')
    d.shape = 'RECTANGLE'
    d.size, d.size_y, d.energy = sx, sy, pot
    o = bpy.data.objects.new("l", d)
    bpy.context.collection.objects.link(o)
    o.location = pos
    o.rotation_euler = mirar(pos, objetivo)


def main():
    os.makedirs(SAL, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=os.path.join(RAIZ, arg("--blend",
                                                             "cad/carro-luces.blend")))
    ob = bpy.data.objects["Carroceria"]
    vs = [v.co for v in ob.data.vertices]
    L = max(v.x for v in vs)
    H = max(v.y for v in vs)
    W = max(v.z for v in vs) * 2
    suelo_y = -0.030 * H / 0.970          # la peana recortada devuelve el piso real
    foco = Vector((L / 2, H * 0.45, 0.0))
    print(f"MODELO         {L:.3f} x {W:.3f} x {H:.3f} m   piso y={suelo_y:.3f}")

    piso = bpy.data.meshes.new("Piso")
    piso.from_pydata([(-30, suelo_y, -30), (30, suelo_y, -30),
                      (30, suelo_y, 30), (-30, suelo_y, 30)], [], [(0, 1, 2, 3)])
    piso.update()
    mp = bpy.data.materials.new("Piso")
    mp.use_nodes = True
    bp = mp.node_tree.nodes["Principled BSDF"]
    bp.inputs["Base Color"].default_value = (0.045, 0.048, 0.055, 1)
    bp.inputs["Roughness"].default_value = 0.42
    piso.materials.append(mp)
    bpy.context.collection.objects.link(bpy.data.objects.new("Piso", piso))

    w = bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.035, 0.038, 0.045, 1)
    # Potencias bajas a proposito: la pintura es oscura (sRGB 115,106,102, muestreada
    # de la lamina del usuario) y con paneles de 1000 W AgX la sube a beige. Si la
    # carroceria sale clara, el problema es la luz, no el material.
    area((L / 2, 4.6, -1.4), foco, 9, 3.5, 260)      # clave, alta y de lado
    area((L / 2, 3.2, 3.6), foco, 6, 3, 130)         # relleno opuesto
    area((-3.2, 2.2, 2.2), (0.5, H * 0.4, 0), 4, 3, 110)    # recorta el morro
    area((L + 3.2, 2.2, -2.2), (L - 0.5, H * 0.4, 0), 4, 3, 110)   # recorta la cola

    e = bpy.context.scene
    e.render.engine = 'CYCLES'
    e.cycles.device = 'CPU'
    e.cycles.samples = int(arg("--muestras", "64"))
    e.cycles.use_denoising = True
    e.view_settings.view_transform = 'AgX'
    e.view_settings.look = 'AgX - Medium High Contrast'
    e.render.resolution_x = 1400
    e.render.resolution_y = 880

    esquinas = [(ex, ey, ez) for ex in (0.0, L) for ey in (suelo_y, H)
                for ez in (-W / 2, W / 2)]
    aspecto = e.render.resolution_x / e.render.resolution_y
    for nom, (dirn, holgura) in VISTAS.items():
        cd = bpy.data.cameras.new("c")
        cd.type = 'ORTHO'
        c = bpy.data.objects.new("c", cd)
        bpy.context.collection.objects.link(c)
        c.location = foco + Vector(dirn).normalized() * 16
        cd.ortho_scale = encuadre(esquinas, c.location, foco, aspecto, holgura)
        c.rotation_euler = mirar(c.location, foco)
        e.camera = c
        e.render.filepath = os.path.join(SAL, nom + ".png")
        bpy.ops.render.render(write_still=True)
        print("FOTO " + nom)


main()
