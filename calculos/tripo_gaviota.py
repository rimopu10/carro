# -*- coding: utf-8 -*-
"""
Juguete 1:N de la carrocería de Tripo con PUERTAS DE GAVIOTA que abren y ruedas que
giran. Parte del sólido real de render/tripo_base.py.

Diferencias con calculos/tripo_juguete.py (el de una pieza):
  * La cabina queda HUECA con el interior que modeló Tripo (asientos, tablero), y los
    cristales se cierran como una LÁMINA de CRISTAL_MM a escala: casco convexo por
    tramos menos el mismo casco erosionado y prolongado hacia el piso. Así no queda
    ni una placa a la altura de la cintura ni paredes entre tramos.
  * Las puertas se cortan con el contorno que trae el modelo (línea detrás de la rueda
    delantera, curva hacia la trasera, estribo abajo) y suben por el cristal hasta el
    ESPINAZO del techo (|z| = 150 mm, el mismo eje de bisagra del chasis real).
  * Bisagra: eje a lo largo del carro sobre la superficie del techo en el espinazo
    (y = 1100). Con el eje EN la superficie, al abrir la puerta su piel gira hacia
    afuera y no choca con la franja central. Nudillos de carrocería adelante y atrás,
    nudillo de la puerta al centro, pasador de filamento 1.75 metido por la cara
    delantera del nudillo de adelante, que asoma sobre el techo.

    python calculos/tripo_gaviota.py [--escala 20]

Salida en impresion/ (piezas acostadas para la cama) y en cad/_gaviota-1aN/ (las mismas
piezas en su lugar, para armar la escena de Blender con render/abrir_gaviota.py).
"""
import argparse
import json
import os
import sys

import manifold3d as mf
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from maqueta import a_cama, a_manifold, a_trimesh, gota, guardar, reporte  # noqa: E402
from tripo_juguete import EJES_X, R_LLANTA, Y_EJE, Z_EXT, ruedas_que_giran  # noqa: E402

RAIZ = os.path.join(HERE, "..")
SOLIDO = os.path.join(RAIZ, "cad", "carroceria-tripo-solida-mm.stl")

# ---- medidas a ESCALA (mm de la pieza impresa) -----------------------------------
CRISTAL_MM = 1.2          # lámina de cristal
HOLGURA_MM = 0.30         # aire entre puerta y carrocería
NUDILLO_MM = 2.0          # radio de los nudillos de la bisagra
PASADOR_LIBRE_MM = 2.1    # agujero de la puerta: gira libre sobre el filamento
PASADOR_FIJO_MM = 1.90    # agujero de la carrocería: el filamento entra justo

# ---- geometría de la puerta, en mm REALES (ejes del proyecto) -----------------------
# contorno visto de lado (x, y), trazado sobre las líneas que trae el modelo de Tripo
CONTORNO_LADO = [(1220, 280), (1220, 740), (1250, 780), (1580, 1040), (1620, 1400),
                 (2080, 1400), (2100, 1060), (2230, 800), (2210, 600), (2150, 450),
                 (2060, 330), (2000, 280)]
# sección (z, y) del lado derecho: lo que queda AFUERA de esta línea es puerta. Por
# dentro deja la cabina (asientos en |z| 100-520, cabeceras hasta ~0.95 m)
Z_ESPINAZO = 150.0
SECCION = [(Z_ESPINAZO, 1400), (2000, 1400), (2000, 150), (600, 150), (600, 750),
           (450, 985), (Z_ESPINAZO, 985)]
# la PUERTA sólo se lleva la piel: por dentro llega a |z| = 720 (la piel del costado va
# en 800-890, así que queda de 80-170 mm reales, 4-8 mm a 1:20). El hueco de la
# carrocería sí llega a 600 (SECCION), así que el panel interior de la puerta se va y la
# cabina queda abierta al levantarla.
SECCION_PUERTA = [(Z_ESPINAZO, 1400), (2000, 1400), (2000, 150), (720, 150), (720, 750),
                  (470, 985), (Z_ESPINAZO, 985)]
# bisagra: eje en x, a la altura del techo sobre el espinazo
Y_BISAGRA = 1100.0
NUDILLOS_CARROCERIA = [(1680, 1760), (1980, 2060)]
NUDILLO_PUERTA = (1780, 1960)

Y_CINTURA = 770.0


def invernadero_hueco(M, esc):
    """Cierra los cristales como lámina de CRISTAL_MM (a escala) y deja la cabina como
    la modeló Tripo. Casco convexo por tramos (como en tripo_juguete) MENOS el casco
    erosionado el grueso del cristal y prolongado hasta el piso de la cabina."""
    t = CRISTAL_MM * esc
    V = np.asarray(M.to_mesh().vert_properties)[:, :3]
    corte = np.where((V[:, 0] > 850) & (V[:, 0] < 2300), 748.0, Y_CINTURA)
    V = V[V[:, 1] >= corte]
    cascos, huecos = [], []
    bola = mf.Manifold.sphere(t, 16)
    for x in np.arange(V[:, 0].min(), V[:, 0].max(), 50.0):
        sel = V[(V[:, 0] >= x) & (V[:, 0] <= x + 100.0)]
        if len(sel) < 8:
            continue
        H = mf.Manifold.hull_points(sel.astype(np.float32))
        cascos.append(H)
        E = H.minkowski_difference(bola)
        if E.is_empty():
            continue
        ev = np.asarray(E.to_mesh().vert_properties)[:, :3]
        abajo = ev.copy()
        abajo[:, 1] = 250.0                      # hasta el piso de la cabina
        huecos.append(mf.Manifold.hull_points(np.vstack([ev, abajo]).astype(np.float32)))
    H = mf.Manifold.batch_boolean(cascos, mf.OpType.Add)
    K = mf.Manifold.batch_boolean(huecos, mf.OpType.Add)
    return M + (H - K), len(cascos)


def _ccw(pts):
    """manifold3d sólo rellena contornos antihorarios (área positiva)."""
    p = np.asarray(pts, float)
    area = 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])
    return p[::-1].tolist() if area < 0 else p.tolist()


def prisma_puerta(lado, crece, seccion=None):
    """Volumen que ocupa la puerta (crece > 0: más grande, para cortar la carrocería;
    crece < 0: más chico, para la puerta). Prisma del contorno de lado ∩ prisma de la
    sección, espejado para el lado izquierdo."""
    a = mf.CrossSection([_ccw(CONTORNO_LADO)]).offset(crece, mf.JoinType.Round)
    lat = mf.Manifold.extrude(a, 4000.0).translate([0, 0, -2000.0])          # (x, y) a lo largo de z
    b = mf.CrossSection([_ccw(seccion or SECCION)]).offset(crece, mf.JoinType.Round)
    sec = mf.Manifold.extrude(b, 6000.0).translate([0, 0, -1000.0])          # (z, y) a lo largo de "x"
    sec = sec.transform(np.array([[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0]], float))  # -> (x, y, z)
    P = lat ^ sec
    return P if lado > 0 else P.mirror([0, 0, 1])


def cilindro_x(x0, x1, r, y, z, n=48):
    return mf.Manifold.cylinder(x1 - x0, r, r, n).transform(
        np.array([[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0]], float)).translate([x0, y, z])


def puertas_gaviota(cuerpo, esc):
    g = HOLGURA_MM * esc / 2
    rk = NUDILLO_MM * esc
    puertas = []
    for lado in (1, -1):
        zb = lado * Z_ESPINAZO
        puerta = cuerpo ^ prisma_puerta(lado, -g, SECCION_PUERTA)
        cuerpo = cuerpo - prisma_puerta(lado, +g)
        kb = [cilindro_x(a, b, rk, Y_BISAGRA, zb) for a, b in NUDILLOS_CARROCERIA]
        kd = cilindro_x(*NUDILLO_PUERTA, rk, Y_BISAGRA, zb)
        # cada nudillo se abre paso en la pieza de enfrente, con holgura
        cuerpo = cuerpo - cilindro_x(NUDILLO_PUERTA[0] - g * 2, NUDILLO_PUERTA[1] + g * 2,
                                     rk + 2 * g, Y_BISAGRA, zb)
        for a, b in NUDILLOS_CARROCERIA:
            puerta = puerta - cilindro_x(a - g * 2, b + g * 2, rk + 2 * g, Y_BISAGRA, zb)
        cuerpo = cuerpo + mf.Manifold.batch_boolean(kb, mf.OpType.Add)
        puerta = puerta + kd
        # pasador: entra por la cara delantera del nudillo de adelante (que asoma sobre el
        # techo detrás del parabrisas), fijo en la carrocería, libre en la puerta; ciego
        # 2 mm antes del final del nudillo de atrás
        cuerpo = cuerpo - cilindro_x(NUDILLOS_CARROCERIA[0][0] - 5, NUDILLOS_CARROCERIA[1][1] - 2 * esc,
                                     PASADOR_FIJO_MM * esc / 2, Y_BISAGRA, zb, 24)
        puerta = puerta - cilindro_x(NUDILLO_PUERTA[0] - 10, NUDILLO_PUERTA[1] + 10,
                                     PASADOR_LIBRE_MM * esc / 2, Y_BISAGRA, zb, 24)
        piezas = puerta.decompose()
        puerta = max(piezas, key=lambda p: p.volume())
        puertas.append((lado, puerta))
    return cuerpo, puertas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--escala", type=int, default=20)
    a = ap.parse_args()
    esc = a.escala
    k = 1.0 / esc
    tm = trimesh.load(SOLIDO)
    tm = max(tm.split(only_watertight=False), key=lambda p: p.volume)
    M = a_manifold(tm)
    M, n = invernadero_hueco(M, esc)
    print(f"cristal: lámina de {CRISTAL_MM} mm a escala en {n} tramos; cabina hueca con el interior de Tripo")
    cuerpo, ruedas = ruedas_que_giran(M, esc)
    cuerpo, puertas = puertas_gaviota(cuerpo, esc)
    cuerpo = max(cuerpo.decompose(), key=lambda p: p.volume())

    ens = os.path.join(RAIZ, "cad", f"_gaviota-1a{esc}")
    os.makedirs(ens, exist_ok=True)

    def en_su_lugar(m, nom):
        a_trimesh(m.scale([k, k, k])).export(os.path.join(ens, nom))

    en_su_lugar(cuerpo, "carroceria.stl")
    for lado, p in puertas:
        en_su_lugar(p, f"puerta-{'der' if lado > 0 else 'izq'}.stl")
    for i, (x, lado, r) in enumerate(ruedas):
        en_su_lugar(r, f"rueda-{i}.stl")
    json.dump({"escala": esc, "bisagra": {"y": Y_BISAGRA, "z": Z_ESPINAZO,
                                          "x": [NUDILLOS_CARROCERIA[0][0], NUDILLOS_CARROCERIA[1][1]]},
               "ejes_x": EJES_X, "y_eje": Y_EJE, "z_ext": Z_EXT},
              open(os.path.join(ens, "datos.json"), "w", encoding="utf-8"), indent=1)

    # piezas para la cama
    piezas = [(f"gaviota-1a{esc}-carroceria.stl", a_cama(cuerpo.scale([k, k, k])))]
    for lado, p in puertas:
        # parada como va en el carro: apoyada en su canto de abajo (el estribo, plano por
        # el corte), costado vertical y el pedazo de techo arriba con soporte por dentro
        piezas.append((f"gaviota-1a{esc}-puerta-{'der' if lado > 0 else 'izq'}.stl",
                       a_cama(p.scale([k, k, k]))))
    juego = mf.Manifold()
    d = 2 * R_LLANTA * k + 4
    for i, (x, lado, r) in enumerate(ruedas):
        r = r.translate([-x, -Y_EJE, 0]).scale([k, k, k])
        if lado < 0:
            r = r.rotate([180, 0, 0])
        lo = r.bounding_box()
        juego = juego + r.translate([(i % 2) * d, (i // 2) * d, -lo[2]])
    piezas.append((f"gaviota-1a{esc}-ruedas-x4.stl", juego))
    for nom, p in piezas:
        reporte(nom, p)
        guardar(p, nom)
    largo_pasador = (NUDILLOS_CARROCERIA[1][1] - 2 * esc - NUDILLOS_CARROCERIA[0][0]) * k
    print(f"   pasadores de bisagra: 2 tramos de filamento 1.75 de {largo_pasador:.0f} mm, "
          f"entran por el frente del nudillo delantero, sobre el techo")
    print(f"   ejes de rueda: 2 tramos de {2 * Z_EXT * k - 1:.0f} mm")


if __name__ == "__main__":
    main()
