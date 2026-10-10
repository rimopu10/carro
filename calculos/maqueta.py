# -*- coding: utf-8 -*-
"""
Maqueta imprimible de la carrocería v3 (vista previa del diseño antes del RC).

Toma las piezas que deja `render/carro_v3.py --maqueta N` en cad/_maqueta-1aN/ (la piel,
lo que se le suma y lo que se le resta, en mm reales) y con manifold3d arma un sólido
cerrado, lo escala a 1:N, lo acuesta para la cama (Z arriba, apoyado en el piso de la
piel) y lo deja en impresion/. Si no cabe en la cama lo parte en un plano X con
agujeros para pernos de filamento.

Además genera las 4 ruedas (llanta + rin de una pieza, acostadas), las arandelas que
las separan del fondo del pozo y una regla de tolerancias para elegir el agujero del
cubo con TU impresora antes de imprimir las ruedas.

    blender --background --python render/carro_v3.py -- --sin-render --maqueta 16
    python calculos/maqueta.py 16                 # una pieza, 211 mm
    python calculos/maqueta.py 12 --partir 2150   # dos piezas cortadas en x=2.15 m

Por qué manifold3d y no Blender: el solver exacto de Blender sobre la piel ya cortada
dejaba aristas abiertas, y una unión con el splitter hasta BAJABA el volumen. Un STL
con huecos le da al slicer capas fantasma; manifold garantiza un sólido.
"""
import argparse
import json
import math
import os

import manifold3d as mf
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(HERE, "..")
SALIDA = os.path.join(RAIZ, "impresion")

CAMA_MM = 220.0               # Ender 3 V3 SE: 220 x 220 x 250
MARGEN_MM = 4.0               # sin brim; deja aire a la línea de purga
PLA_G_CM3 = 1.24


# ---------------------------------------------------------------------------
# utilería manifold <-> trimesh
# ---------------------------------------------------------------------------
def a_manifold(tm):
    tm = trimesh.Trimesh(tm.vertices, tm.faces, process=True)
    tm.merge_vertices()
    m = mf.Manifold(mf.Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                            tri_verts=np.asarray(tm.faces, np.uint32)))
    if m.status() != mf.Error.NoError or m.is_empty():
        # último recurso: que trimesh cierre lo que pueda
        trimesh.repair.fill_holes(tm)
        trimesh.repair.fix_normals(tm)
        m = mf.Manifold(mf.Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                                tri_verts=np.asarray(tm.faces, np.uint32)))
    if m.status() != mf.Error.NoError:
        raise RuntimeError(f"malla no reparable: {m.status()}")
    return m


def cargar(ruta):
    return a_manifold(trimesh.load(ruta, force="mesh"))


def a_trimesh(m):
    me = m.to_mesh()
    return trimesh.Trimesh(np.asarray(me.vert_properties)[:, :3], np.asarray(me.tri_verts),
                           process=False)


def a_cama(m):
    """Ejes del proyecto (X largo, Y alto, Z lateral) -> impresora (Z arriba): la pieza
    apoyada en el piso de la piel. (x, y, z) -> (x, -z, y) es rotación propia."""
    R = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0]], float)
    m = m.transform(R)
    lo, hi = np.array(m.bounding_box()[:3]), np.array(m.bounding_box()[3:])
    c = (lo + hi) / 2
    return m.translate([-c[0], -c[1], -lo[2]])


def gota(d, largo, eje="z"):
    """Prisma de sección en gota (punta a 45°), a lo largo de `eje`, centrado. La
    punta va hacia +Z de la CAMA una vez orientado (ver a_cama)."""
    r = d / 2
    pts = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
           for a in range(-225, 46, 15)] + [(0.0, r * math.sqrt(2))]
    cs = mf.CrossSection([pts])
    p = mf.Manifold.extrude(cs, largo).translate([0, 0, -largo / 2])
    if eje == "x":            # sección en el plano (z, y) del proyecto -> extruida en x
        p = p.transform(np.array([[0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0]], float))
    return p


def reporte(nombre, m):
    lo, hi = np.array(m.bounding_box()[:3]), np.array(m.bounding_box()[3:])
    dim = hi - lo
    vol = m.volume() / 1000.0                                # cm3
    area = m.surface_area() / 100.0                          # cm2
    # 3 perímetros + 5 capas arriba/abajo ~ 1.2 mm de cáscara; relleno giroide 12 %
    cascara = min(vol, area * 0.12)
    gramos = (cascara + 0.12 * max(vol - cascara, 0)) * PLA_G_CM3
    cabe = dim[0] <= CAMA_MM - MARGEN_MM and dim[1] <= CAMA_MM - MARGEN_MM and dim[2] <= 250
    print(f"   {nombre:34s} {dim[0]:6.1f} x {dim[1]:6.1f} x {dim[2]:5.1f} mm  "
          f"~{gramos:4.0f} g PLA  {'CABE' if cabe else 'NO CABE'}")
    return cabe, gramos


def guardar(m, nombre):
    os.makedirs(SALIDA, exist_ok=True)
    tm = a_trimesh(m)
    ruta = os.path.join(SALIDA, nombre)
    tm.export(ruta)
    assert tm.is_watertight, f"{nombre} no es hermético"
    return ruta


# ---------------------------------------------------------------------------
# carrocería
# ---------------------------------------------------------------------------
def carroceria(escala, partir_x=None):
    d = os.path.join(RAIZ, "cad", f"_maqueta-1a{escala}")
    datos = json.load(open(os.path.join(d, "datos.json"), encoding="utf-8"))
    piel = cargar(os.path.join(d, "piel.stl"))
    v0 = piel.volume()
    archivos = sorted(os.listdir(d))
    for f in archivos:
        if f.startswith("sumar-"):
            piel = piel + cargar(os.path.join(d, f))
    v1 = piel.volume()
    for f in archivos:
        if f.startswith("restar-"):
            piel = piel - cargar(os.path.join(d, f))
    v2 = piel.volume()
    print(f"   volumen real: piel {v0/1e9:.3f} m3, +sumas {(v1-v0)/1e6:+.1f} L, "
          f"-surcos/ejes {(v2-v1)/1e6:+.2f} L  ->  genus {piel.genus()}")
    k = 1.0 / escala
    piel = piel.scale([k, k, k])
    piezas = []
    if partir_x is None:
        piezas.append(("carroceria", piel))
    else:
        xc = partir_x * k
        adelante, atras = piel.split_by_plane([1, 0, 0], xc)
        # (split_by_plane: la primera es la del lado al que apunta la normal)
        adelante, atras = atras, adelante
        # pernos: tramos de filamento 1.75 en agujeros de gota de 2.2, 6 mm por lado.
        # Posiciones (z, y) reales que caen en material macizo en x = 2.15 m
        hueco = mf.Manifold()
        for (z, y) in ((0.0, 420.0), (430.0, 360.0), (-430.0, 360.0), (0.0, 230.0)):
            hueco = hueco + gota(2.2, 12.0, eje="x").translate([xc, y * k, z * k])
        adelante, atras = adelante - hueco, atras - hueco
        piezas += [("carroceria-frente", adelante), ("carroceria-cola", atras)]
    salidas = []
    for nom, p in piezas:
        p = a_cama(p)
        salidas.append((f"maqueta-1a{escala}-{nom}.stl", p))
    return salidas, datos


# ---------------------------------------------------------------------------
# ruedas, arandelas y regla de tolerancias
# ---------------------------------------------------------------------------
def rueda(R, W, rin_pulg, escala, agujero):
    """Rueda acostada, cara interior en la cama. Llanta con hombro redondeado, rin
    rebajado en la cara exterior con 10 rayos en pares y tapón central."""
    k = 1000.0 / escala
    r, w = R * k, W * k
    rr = rin_pulg * 25.4 / 2 / escala                     # radio del rin
    ch = min(0.12 * w, 0.06 * r)                          # redondeo del hombro
    perfil = [(0.0, 0.0), (r - ch, 0.0), (r, ch), (r, w - ch), (r - ch, w),
              (rr + 0.4, w), (rr + 0.4, w - 0.3), (0.0, w - 0.3)]
    m = mf.Manifold.revolve(mf.CrossSection([perfil]), 96)
    # rebaje del rin: 0.6 mm
    hondo = 0.6
    m = m - mf.Manifold.cylinder(hondo + 1, rr, rr, 96).translate([0, 0, w - 0.3 - hondo])
    # 10 rayos en pares, de 0.9 mm, hasta el borde del rin
    for i in range(10):
        a = 2 * math.pi * i / 10 + (0.09 if i % 2 else -0.09)
        L = rr - 1.2
        rayo = mf.Manifold.cube([L, 0.9, hondo + 0.05]).translate([1.2, -0.45, 0])
        rayo = rayo.rotate([0, 0, math.degrees(a)])
        m = m + rayo.translate([0, 0, w - 0.3 - hondo])
    m = m + mf.Manifold.cylinder(hondo + 0.3, 2.0, 2.0, 48).translate([0, 0, w - 0.3 - hondo])
    m = m - mf.Manifold.cylinder(3 * w, agujero / 2, agujero / 2, 32).translate([0, 0, -w])
    return m


def arandela(largo, d_int):
    return (mf.Manifold.cylinder(largo, 2.2, 2.2, 48)
            - mf.Manifold.cylinder(largo * 3, d_int / 2, d_int / 2, 32).translate([0, 0, -largo]))


def regla_tolerancias():
    """Placa con agujeros VERTICALES de 1.70 a 2.00 (para el cubo de la rueda, a
    presión sobre filamento 1.75) y una pared con agujeros HORIZONTALES en gota de
    2.0 a 2.3 (para el eje en la carrocería, que debe girar libre). De menor a mayor,
    de izquierda a derecha; la muesca marca el lado chico."""
    base = mf.Manifold.cube([62, 12, 3])
    for i, d in enumerate(np.arange(1.70, 2.0001, 0.05)):
        base = base - mf.Manifold.cylinder(10, d / 2, d / 2, 32).translate([5 + 8.5 * i, 6, -1])
    pared = mf.Manifold.cube([62, 4, 10]).translate([0, 12, 0])
    for i, d in enumerate((2.0, 2.1, 2.2, 2.3)):
        g = gota(d, 10.0, eje="z")                                   # eje en z...
        g = g.transform(np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0]], float))  # ...a y, punta a +z
        pared = pared - g.translate([8 + 15 * i, 14, 5.5])
    muesca = mf.Manifold.cube([3, 3, 10]).translate([-1.5, 4.5, -1])
    return (base + pared) - muesca


def ruedas(datos, escala, agujero_cubo):
    salidas = []
    vistos = set()
    for w in datos["ruedas"]:
        clave = (round(w["R"], 4), w["rin"])
        if clave in vistos:
            continue
        vistos.add(clave)
        nom = "delantera" if w["x"] < 1.0 else "trasera"
        m = rueda(w["R"], w["W"], w["rin"], escala, agujero_cubo)
        # dos por eje, lado a lado
        dx = 2 * w["R"] * 1000 / escala + 3
        par = m + m.translate([dx, 0, 0])
        salidas.append((f"maqueta-1a{escala}-ruedas-{nom}-x2.stl", par))
    # arandelas: cara interior de la llanta (|z| - W/2) menos el fondo del pozo, -0.2 de juego
    z_in = min(abs(w["z"]) - w["W"] / 2 for w in datos["ruedas"])
    largo = (z_in - datos["z_pozo"]) * 1000 / escala - 0.2
    ar = mf.Manifold()
    for i in range(4):
        ar = ar + arandela(largo, datos["eje_mm"]).translate([6 * i, 0, 0])
    salidas.append((f"maqueta-1a{escala}-arandelas-x4.stl", ar))
    return salidas, largo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("escala", type=int)
    ap.add_argument("--partir", type=float, default=None,
                    help="x real en mm del plano de corte (p.ej. 2150 = pierna trasera de la puerta)")
    ap.add_argument("--agujero-cubo", type=float, default=1.85,
                    help="Ø del agujero de la rueda en mm (sale de la regla de tolerancias)")
    a = ap.parse_args()

    print(f"MAQUETA 1:{a.escala}  (cama {CAMA_MM:.0f} mm, margen {MARGEN_MM:.0f})")
    piezas, datos = carroceria(a.escala, a.partir)
    rds, largo_ar = ruedas(datos, a.escala, a.agujero_cubo)
    piezas += rds
    piezas.append(("prueba-tolerancias-ejes.stl", regla_tolerancias()))
    total = 0.0
    for nom, m in piezas:
        cabe, g = reporte(nom, m)
        total += g
        guardar(m, nom)
        if not cabe:
            print(f"   ! {nom} no cabe en la cama: usar --partir")
    eje_del = 2 * (datos["ruedas"][0]["z"] + datos["ruedas"][0]["W"] / 2) * 1000 / a.escala
    eje_tras = 2 * (datos["ruedas"][2]["z"] + datos["ruedas"][2]["W"] / 2) * 1000 / a.escala
    print(f"   total ~{total:.0f} g PLA")
    print(f"   ejes: filamento 1.75 cortado a {eje_del - 1:.0f} mm (delantero) y "
          f"{eje_tras - 1:.0f} mm (trasero); arandelas de {largo_ar:.1f} mm entre rueda y pozo")
    print(f"OK  {os.path.normpath(SALIDA)}")


if __name__ == "__main__":
    main()
