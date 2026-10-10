# -*- coding: utf-8 -*-
"""
Juguete impreso (vista tipo Hot Wheels) de la carrocería de Tripo: TODO en una pieza,
con ruedas, luces y cristales como forma, listo para la Ender 3 V3 SE.

Parte del sólido real de render/tripo_base.py (cad/carroceria-tripo-solida-mm.stl).

Cristales laterales: Tripo no los modeló; deja el hueco hacia una cabina vacía bajo un
techo de 45 mm. Impreso así, el techo queda volando sobre una cavidad sin forma de
quitar el soporte. Se cierran como un cristal de verdad: en cortes cada PASO mm a lo
largo del carro, donde el techo sale separado de la carrocería (= ventana abierta), se
toma el casco convexo del techo y de la orilla de las puertas, y entre dos cortes
seguidos se arma el casco 3D. Eso da un cristal recto del borde del techo al de la
puerta, y la cabina queda encerrada: el vacío interior se tira y queda macizo.

    python calculos/tripo_juguete.py                 # 1:20 (una pieza) y 1:64 (Hot Wheels)
    python calculos/tripo_juguete.py --escalas 18
"""
import argparse
import os
import sys

import manifold3d as mf
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from maqueta import CAMA_MM, MARGEN_MM, a_cama, a_manifold, a_trimesh, guardar, reporte  # noqa: E402

RAIZ = os.path.join(HERE, "..")
SOLIDO = os.path.join(RAIZ, "cad", "carroceria-tripo-solida-mm.stl")
PASO = 20.0                     # mm reales entre cortes
Y_TECHO_MIN = 750.0             # una pieza del corte que empieza más arriba es techo
MARGEN_PUERTA = 30.0            # se toma la orilla de la puerta desde 30 mm bajo su tope


def cerrar_invernadero(M, y_cintura=770.0, tramo=100.0, paso=50.0):
    """Cierra TODOS los cristales (Tripo deja abiertos parabrisas, laterales,
    ventanillas y luneta, con la cabina vacía detrás). Todo lo que está por encima de
    la línea de cintura es invernadero; se parte en tramos de `tramo` mm a lo largo del
    carro (traslapados cada `paso`) y cada tramo se cierra con su casco convexo. Por
    tramos y no un solo casco: así el cristal sigue la curva del techo en el perfil y
    no se tiende recto de la cabecera a la cola. Debajo de la cintura no se toca nada
    (cofre, salpicaderas, caderas)."""
    me = M.to_mesh()
    V = np.asarray(me.vert_properties)[:, :3]
    # en la cabina (x 0.85-2.30 m: base del parabrisas y tope de puertas) el cristal
    # arranca a ~0.75 m, más abajo
    # que la cintura; ahí la línea baja a 0.748, justo encima del lomo de las
    # salpicaderas (0.745) para no tender un puente sobre el cofre
    corte = np.where((V[:, 0] > 850) & (V[:, 0] < 2300), 748.0, y_cintura)
    V = V[V[:, 1] >= corte]
    cascos = []
    x0, x1 = V[:, 0].min(), V[:, 0].max()
    for x in np.arange(x0, x1, paso):
        sel = V[(V[:, 0] >= x) & (V[:, 0] <= x + tramo)]
        if len(sel) >= 8:
            cascos.append(mf.Manifold.hull_points(sel.astype(np.float32)))
    if not cascos:
        return M, 0
    return M + mf.Manifold.batch_boolean(cascos, mf.OpType.Add), len(cascos)


def rellenar_cabina(M, paso=10.0, solape=5.0):
    """La cabina bajo el cristal queda hueca y asomada al exterior por algún resquicio,
    así que no sale como vacío encerrado. Se rellena por dentro: en cada corte, cada
    HUECO (contorno interior) se engrosa `solape` mm hacia las paredes y se extruye
    `paso` + 2 mm. Como los huecos están dentro del cuerpo, la piel exterior no se toca."""
    A = np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0]], float)      # x -> eje de corte
    B = np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]], float)      # de regreso
    Ms = M.transform(A)
    x0, x1 = M.bounding_box()[0], M.bounding_box()[3]
    losas, n = [], 0
    for x in np.arange(x0 + paso / 2, x1, paso):
        for r in Ms.slice(float(x)).to_polygons():
            r = np.asarray(r)
            area = 0.5 * np.sum(r[:, 0] * np.roll(r[:, 1], -1) - np.roll(r[:, 0], -1) * r[:, 1])
            if area >= 0 or abs(area) < 400:          # contorno exterior, o hueco minúsculo
                continue
            cs = mf.CrossSection([r[::-1]]).offset(solape, mf.JoinType.Round)
            losas.append(mf.Manifold.extrude(cs, paso + 2.0).translate([0, 0, x - paso / 2 - 1.0]))
            n += 1
    if not losas:
        return M, 0
    relleno = mf.Manifold.batch_boolean(losas, mf.OpType.Add).transform(B)
    return M + relleno, n


def solo_cascaron_exterior(M):
    """Quita los vacíos interiores (la cabina que quedó encerrada) y las astillas."""
    tm = a_trimesh(M)
    piezas = tm.split(only_watertight=False)
    ext = max(piezas, key=lambda p: p.volume)
    return a_manifold(ext), len(piezas) - 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--escalas", default="20,64")
    a = ap.parse_args()
    tm = trimesh.load(SOLIDO)
    tm = max(tm.split(only_watertight=False), key=lambda p: p.volume)
    M = a_manifold(tm)
    v0 = M.volume()
    M, n = cerrar_invernadero(M)
    M, nh = rellenar_cabina(M)
    M, quitados = solo_cascaron_exterior(M)
    print(f"cabina: {nh} huecos interiores rellenados")
    print(f"cristales: invernadero cerrado en {n} tramos; volumen {v0/1e9:.3f} -> "
          f"{M.volume()/1e9:.3f} m3; {quitados} vacíos/astillas fuera")
    for esc in [int(e) for e in a.escalas.split(",")]:
        k = 1.0 / esc
        p = a_cama(M.scale([k, k, k]))
        nom = f"juguete-tripo-1a{esc}.stl"
        cabe, g = reporte(nom, p)
        guardar(p, nom)
        if not cabe:
            print(f"   ! no cabe en la cama de {CAMA_MM:.0f} mm (margen {MARGEN_MM:.0f})")


if __name__ == "__main__":
    main()
