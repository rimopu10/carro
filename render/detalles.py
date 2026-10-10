# -*- coding: utf-8 -*-
"""
Le pone al modelo la GEOMETRIA DURA que la reconstruccion no puede dar: las opticas.

Un reconstructor 3D devuelve volumen. Las luces no son volumen —son un dibujo sobre
la piel— y se pierden enteras en la nube de puntos. Por eso el modelo sale con la
trasera en blanco. Aqui se recuperan de donde si estan: de la lamina de referencia,
via calculos/firma_luces.py, que las aisla por color y las vectoriza.

Como se pegan a la carroceria: NO con un booleano contra un prisma. Las tiras se
enrollan sobre el flanco, y ahi la piel corre casi paralela al eje del carro; un
prisma extruido en X no la corta, la embarra a lo largo de medio metro. Lo que se hace
es rasterizar el poligono en una rejilla fina y PROYECTAR cada nodo sobre la piel con
un rayo. Cada vertice cae exactamente donde la superficie esta, y la optica hereda su
curvatura, tambien donde da la vuelta.

    blender --background --python render/detalles.py -- --glb cad/gem-mv3.glb
"""
import json
import math
import os
import sys

import bpy
import bmesh
import mathutils
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(n, d):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAD = os.path.join(RAIZ, "cad")
CH = json.load(open(os.path.join(CAD, "chasis.json"), encoding="utf-8"))
FIRMA = json.load(open(os.path.join(CAD, "firma-luces.json"), encoding="utf-8"))

EJE_DEL = CH["ruedas"][0]["x"]
EJE_TRAS = CH["ruedas"][2]["x"]
LARGO = float(arg("--largo", "3.35"))
ANCHO = float(arg("--ancho", "1.82"))
EJE_DEL_REF, EJE_TRAS_REF = 0.202, 0.832
FRAC_PEDESTAL = 0.030          # cuanto se recorta por abajo al quitar la peana
PASO = float(arg("--paso", "0.002"))    # lado de la celda al rasterizar, en metros
GRUESO = float(arg("--grueso", "0.006"))   # espesor de la optica
SALIENTE = 0.0006              # cuanto se despega de la piel, para que no haya z-fight


# ---------------------------------------------------------------- carga y encuadre
def caja(o):
    vs = [v.co for v in o.data.vertices]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return mn, mx, mx - mn


def cargar_y_limpiar(glb):
    bpy.ops.import_scene.gltf(filepath=glb)
    ms = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in ms:
        o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    if len(ms) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    mn, mx, d = caja(ob)
    if d.y > d.x:
        ob.data.transform(mathutils.Matrix.Rotation(math.radians(-90), 4, 'Z'))
        ob.data.update()
        mn, mx, d = caja(ob)
    if d.z > d.y:
        ob.data.transform(mathutils.Matrix.Rotation(math.radians(90), 4, 'X'))
        ob.data.update()
        mn, mx, d = caja(ob)

    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                           plane_co=(0, 0, mn.z + d.z * FRAC_PEDESTAL),
                           plane_no=(0, 0, 1), clear_inner=True)
    # cerrar el fondo. Sin esto el carro es una cascara abierta: se ve el hueco negro
    # bajo el splitter y ningun laminador lo acepta como solido para imprimir.
    borde = [e for e in bm.edges if len(e.link_faces) == 1]
    if borde:
        tapa = bmesh.ops.holes_fill(bm, edges=borde)["faces"]
        # holes_fill devuelve UN n-gono gigante; sin trocearlo el sombreado suave lo
        # vuelve una mancha y el triangulador del exportador lo revienta
        bmesh.ops.poke(bm, faces=tapa)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()

    vs = [v.co for v in ob.data.vertices]
    x0, x1 = min(v.x for v in vs), max(v.x for v in vs)
    L = x1 - x0
    ini = [v.z for v in vs if v.x < x0 + 0.10 * L]
    fin = [v.z for v in vs if v.x > x1 - 0.10 * L]
    if sum(ini) / len(ini) > sum(fin) / len(fin):
        ob.data.transform(mathutils.Matrix.Rotation(math.radians(180), 4, 'Z'))
        ob.data.update()

    ob.data.transform(mathutils.Matrix.Rotation(math.radians(-90), 4, 'X'))
    ob.data.update()

    mn, mx, d = caja(ob)
    s = ANCHO / d.z
    x_ref = [mn.x, mn.x + EJE_DEL_REF * d.x, mn.x + EJE_TRAS_REF * d.x, mx.x]
    x_nos = [0.0, EJE_DEL, EJE_TRAS, LARGO]
    for v in ob.data.vertices:
        v.co.x = float(np.interp(v.co.x, x_ref, x_nos))
        v.co.y = (v.co.y - mn.y) * s
        v.co.z = (v.co.z - (mn.z + mx.z) / 2) * s
    ob.data.update()
    mn, mx, d = caja(ob)
    ob.name = "Carroceria"
    print(f"CARROCERIA     {len(ob.data.polygons)} caras · "
          f"{d.x:.3f} x {d.z:.3f} x {d.y:.3f} m")
    return ob, d


# ---------------------------------------------------------------- opticas
def dentro(pol, pts):
    """Par-impar vectorizado. Vale para la firma en Y, que tiene brazos y no es
    convexa ni por asomo."""
    x, y = pts[:, 0], pts[:, 1]
    est = np.zeros(len(pts), bool)
    n = len(pol)
    j = n - 1
    for i in range(n):
        xi, yi = pol[i]
        xj, yj = pol[j]
        cruza = ((yi > y) != (yj > y)) & \
                (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
        est ^= cruza
        j = i
    return est


def optica(pol_uv, semi, y0, alto, arbol, desde_x, signo, nombre):
    """Rasteriza el poligono en (lateral, altura) y proyecta cada nodo sobre la piel."""
    pol = np.array([[u * semi, y0 + v * alto] for u, v in pol_uv])
    z0, z1 = pol[:, 0].min(), pol[:, 0].max()
    w0, w1 = pol[:, 1].min(), pol[:, 1].max()
    nz = int((z1 - z0) / PASO) + 2
    nw = int((w1 - w0) / PASO) + 2
    zz = z0 + np.arange(nz) * PASO
    ww = w0 + np.arange(nw) * PASO
    G = np.stack(np.meshgrid(zz, ww, indexing="ij"), -1).reshape(-1, 2)
    est = dentro(pol, G).reshape(nz, nw)
    if est.sum() < 4:
        return None

    R = 6.0
    idx = -np.ones((nz, nw), int)
    verts, nrm = [], []
    for i in range(nz):
        for j in range(nw):
            if not est[i, j]:
                continue
            o = Vector((desde_x, float(ww[j]), float(zz[i])))
            g = arbol.ray_cast(o, Vector((signo, 0.0, 0.0)), R)
            if g[0] is None:
                est[i, j] = False
                continue
            idx[i, j] = len(verts)
            verts.append(g[0] + g[1] * SALIENTE)
            nrm.append(g[1])

    caras = []
    for i in range(nz - 1):
        for j in range(nw - 1):
            a, b, c, d = idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]
            if min(a, b, c, d) >= 0:
                caras.append((a, b, c, d))
    if not caras:
        return None

    me = bpy.data.meshes.new(nombre)
    me.from_pydata([tuple(v) for v in verts], [], caras)
    me.validate()
    me.update()
    # normales hacia fuera: la media debe apuntar en el mismo sentido que los rayos
    # que las encontraron, o el Solidify crecera hacia dentro del carro
    if sum(p.normal.x for p in me.polygons) * signo > 0:
        me.flip_normals()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.collection.objects.link(ob)
    m = ob.modifiers.new("g", 'SOLIDIFY')
    m.thickness = GRUESO
    m.offset = 1.0
    print(f"    {nombre:14s} {len(verts):6d} nodos  {len(caras):6d} caras")
    return ob


def pintar_oscuras(cuerpo, semi, y0, alto):
    """Asigna el material oscuro a las caras que caen dentro de la parrilla o el difusor.

    Va por MATERIAL, no por booleano: la parrilla y el difusor ya existen como volumen
    en la reconstruccion —estan hundidos y con relieve—, lo unico que les falta es
    dejar de ser color carroceria. Un booleano ahi solo agregaria un millon de caras
    para no cambiar nada de la forma.
    """
    me = cuerpo.data
    n = len(me.polygons)
    cen = np.empty(n * 3)
    nor = np.empty(n * 3)
    me.polygons.foreach_get("center", cen)
    me.polygons.foreach_get("normal", nor)
    cen = cen.reshape(n, 3)
    nor = nor.reshape(n, 3)
    idx = np.zeros(n, dtype=np.int32)

    for clave, lado in (("oscuro_frontal", -1.0), ("oscuro_trasera", +1.0)):
        # solo las caras que MIRAN hacia esa vista, o el poligono del frente pintaria
        # tambien la cola: en proyeccion las dos ocupan el mismo (u,v)
        cand = (nor[:, 0] * lado > 0.05)
        cand &= (cen[:, 0] < 0.40 * LARGO) if lado < 0 else (cen[:, 0] > 0.60 * LARGO)
        if not cand.any():
            continue
        uv = np.stack([cen[cand, 2] / semi, (cen[cand, 1] - y0) / alto], -1)
        marca = np.zeros(cand.sum(), bool)
        for pol in FIRMA[clave]:
            marca |= dentro(np.array(pol), uv)
        sub = np.flatnonzero(cand)[marca]
        idx[sub] = 1
        print(f"    {clave:15s} {len(sub):7d} caras")

    me.polygons.foreach_set("material_index", idx)
    me.update()


def mat_luz(nombre, color, fuerza):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = 0.08
    b.inputs["Emission Color"].default_value = (*color, 1.0)
    b.inputs["Emission Strength"].default_value = fuerza
    return m


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    cuerpo, d = cargar_y_limpiar(os.path.join(RAIZ, arg("--glb", "cad/gem-mv3.glb")))

    bm = bmesh.new()
    bm.from_mesh(cuerpo.data)
    arbol = BVHTree.FromBMesh(bm)

    # v se midio con v=0 en el borde inferior de la lamina, que es la peana; el modelo
    # ya viene recortado ahi, asi que hay que devolver ese trozo antes de mapear
    alto = d.y / (1.0 - FRAC_PEDESTAL)
    y0 = -FRAC_PEDESTAL * alto
    semi = d.z / 2.0

    piezas = []
    for k, pol in enumerate(FIRMA["luz_frontal"], 1):
        o = optica(pol, semi, y0, alto, arbol, -1.5, +1.0, f"LuzDel{k}")
        if o:
            piezas.append((o, "del"))
    for k, pol in enumerate(FIRMA["luz_trasera"], 1):
        o = optica(pol, semi, y0, alto, arbol, LARGO + 1.5, -1.0, f"LuzTras{k}")
        if o:
            piezas.append((o, "tras"))
    bm.free()
    md = mat_luz("LuzDelantera", (0.62, 0.80, 1.0), 3.0)
    mt = mat_luz("LuzTrasera", (1.0, 0.06, 0.03), 2.6)
    for o, lado in piezas:
        o.data.materials.append(md if lado == "del" else mt)

    mp = bpy.data.materials.new("Pintura")
    mp.use_nodes = True
    b = mp.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.173, 0.145, 0.133, 1)
    b.inputs["Metallic"].default_value = 0.22
    b.inputs["Roughness"].default_value = 0.36
    b.inputs["Coat Weight"].default_value = 0.35
    b.inputs["Coat Roughness"].default_value = 0.16

    mn_ = bpy.data.materials.new("Rejilla")
    mn_.use_nodes = True
    bn = mn_.node_tree.nodes["Principled BSDF"]
    bn.inputs["Base Color"].default_value = (0.016, 0.016, 0.018, 1)
    bn.inputs["Metallic"].default_value = 0.0
    bn.inputs["Roughness"].default_value = 0.62

    # limpiar primero: el GLB trae su propio material y las caras siguen apuntando al
    # indice 0, asi que un append a secas deja la carroceria con la pintura del importador
    cuerpo.data.materials.clear()
    cuerpo.data.materials.append(mp)     # indice 0 = pintura
    cuerpo.data.materials.append(mn_)    # indice 1 = parrilla y difusor
    for p in cuerpo.data.polygons:
        p.use_smooth = True
    pintar_oscuras(cuerpo, semi, y0, alto)   # despues de crear las ranuras

    bpy.ops.object.select_all(action='DESELECT')
    for o in [cuerpo] + [p for p, _ in piezas]:
        o.select_set(True)
    bpy.context.view_layer.objects.active = cuerpo
    dest = os.path.join(CAD, "carro-luces.glb")
    bpy.ops.export_scene.gltf(filepath=dest, use_selection=True, export_format='GLB')
    print(f"GLB            {dest}  ({len(piezas)} opticas)")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(CAD, "carro-luces.blend"))


main()
