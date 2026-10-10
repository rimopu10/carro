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


# Ruedas de la carrocería de Tripo (medidas sobre el sólido real, 2026-10-09, histograma
# radial sobre el eje): centro a y = 300; la rodadura termina en ~300 mm de radio (Ø600,
# rin ~17") y el forro del pozo empieza en ~308, casi rozándola (el vóxel de 4 mm los
# funde). Se corta la rueda a 303 y el pozo se abre a 300 + holgura. La llanta ocupa
# |z| 616-883 mm; el arco de la salpicadera queda a ~340 mm del eje.
EJES_X = (550.0, 2680.0)
Y_EJE, R_LLANTA, R_CORTE = 300.0, 297.0, 303.0
R_RIN = 228.0                   # hasta aquí llegan los rayos (perfil lateral, rin ~17")
Z_INT, Z_EXT = 616.0, 883.0


def ruedas_que_giran(M, esc, eje_mm=2.1, cubo_mm=1.85):
    """Separa las 4 ruedas para que giren. Todo se corta a escala real pero las
    holguras y los agujeros se fijan en mm A ESCALA (lo que mide la pieza impresa):
    0.75 mm de aire entre llanta y pozo, eje de filamento 1.75 que gira libre en la
    carrocería (agujero en gota de 2.1) y entra a presión en el cubo (1.85)."""
    mm = float(esc)                                   # 1 mm a escala, en mm reales
    holgura = 0.75 * mm
    ruedas, cuerpo = [], M
    for x in EJES_X:
        for lado in (1, -1):
            z0 = Z_INT - 0.5 * holgura
            cil = mf.Manifold.cylinder(Z_EXT + 40 - z0, R_CORTE, R_CORTE, 128)
            hueco = mf.Manifold.cylinder(1200, R_LLANTA + holgura, R_LLANTA + holgura, 128)
            if lado > 0:
                cil, hueco = cil.translate([x, Y_EJE, z0]), hueco.translate([x, Y_EJE, Z_INT - holgura])
            else:
                cil = cil.translate([x, Y_EJE, -(Z_EXT + 40)])
                hueco = hueco.translate([x, Y_EJE, -(Z_INT - holgura) - 1200])
            # El forro del pozo va casi rozando la llanta y el vóxel los fundió en varios
            # puntos, sin un radio de corte limpio entre los dos. Así que del modelo de
            # Tripo sólo se toma el RIN (rayos, disco, centro: r < R_RIN, donde no hay
            # forro) y la llanta se rehace limpia por revolución con las mismas medidas.
            rin = mf.Manifold.cylinder(Z_EXT + 40 - z0, R_RIN, R_RIN, 128)
            rin = rin.translate([x, Y_EJE, z0] if lado > 0 else [x, Y_EJE, -(Z_EXT + 40)])
            pedazos = (M ^ rin).decompose()
            rin = max(pedazos, key=lambda p: p.volume())
            w = Z_EXT - Z_INT
            h = 0.06 * w                                            # hombro redondeado
            perfil = [(R_RIN - 6, 0), (R_LLANTA - h, 0), (R_LLANTA - h * 0.3, h * 0.3),
                      (R_LLANTA, h), (R_LLANTA, w - h), (R_LLANTA - h * 0.3, w - h * 0.3),
                      (R_LLANTA - h, w), (R_RIN - 6, w)]
            llanta = mf.Manifold.revolve(mf.CrossSection([perfil]), 160)
            llanta = llanta.translate([x, Y_EJE, Z_INT] if lado > 0 else [x, Y_EJE, -Z_EXT])
            ruedas.append((x, lado, rin + llanta))
            cuerpo = cuerpo - hueco
    # ejes: gota (punta arriba) de lado a lado, a la altura del centro de la llanta
    from maqueta import gota
    for x in EJES_X:
        cuerpo = cuerpo - gota(eje_mm * mm, 2400.0, eje="z").translate([x, Y_EJE, 0])
    cubos = []
    for x, lado, r in ruedas:
        agujero = mf.Manifold.cylinder(800, cubo_mm * mm / 2, cubo_mm * mm / 2, 48).translate([x, Y_EJE, -400])
        cubos.append((x, lado, r - agujero))
    return cuerpo, cubos


def solo_cascaron_exterior(M):
    """Quita los vacíos interiores (la cabina que quedó encerrada) y las astillas."""
    tm = a_trimesh(M)
    piezas = tm.split(only_watertight=False)
    ext = max(piezas, key=lambda p: p.volume)
    return a_manifold(ext), len(piezas) - 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--escalas", default="20,64")
    ap.add_argument("--rodante-hasta", type=int, default=32,
                    help="hasta qué escala se hace la versión con ruedas que giran (1:64 es muy chica)")
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
        piezas = [(f"juguete-tripo-1a{esc}.stl", a_cama(M.scale([k, k, k])))]
        if esc <= a.rodante_hasta:
            cuerpo, ruedas = ruedas_que_giran(M, esc)
            piezas.append((f"juguete-tripo-1a{esc}-rodante-carroceria.stl", a_cama(cuerpo.scale([k, k, k]))))
            # las 4 ruedas acostadas (cara interior abajo), en 2 x 2 sobre la cama
            juego = mf.Manifold()
            d = 2 * R_LLANTA * k + 4
            for i, (x, lado, r) in enumerate(ruedas):
                r = r.translate([-x, -Y_EJE, 0]).scale([k, k, k])
                if lado < 0:                       # cara interior hacia -z -> girar
                    r = r.rotate([180, 0, 0])
                lo = r.bounding_box()
                r = r.translate([(i % 2) * d, (i // 2) * d, -lo[2]])
                juego = juego + r
            piezas.append((f"juguete-tripo-1a{esc}-rodante-ruedas-x4.stl", juego))
        for nom, p in piezas:
            cabe, g = reporte(nom, p)
            guardar(p, nom)
            if not cabe:
                print(f"   ! no cabe en la cama de {CAMA_MM:.0f} mm (margen {MARGEN_MM:.0f})")
        if esc <= a.rodante_hasta:
            eje = 2 * Z_EXT * k - 1
            print(f"   ejes 1:{esc}: dos tramos de filamento 1.75 de {eje:.0f} mm; "
                  f"probar antes el cubo con impresion/prueba-tolerancias-ejes.stl")


if __name__ == "__main__":
    main()
