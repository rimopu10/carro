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

    python calculos/tripo_gaviota.py [--escala 20] [--impresora ender3v3se]

Con --impresora se leen impresion/impresoras/NOMBRE.json (holgura de puerta, compensación
de agujeros, brim) y todo sale en impresion/NOMBRE/; sin ella, medidas de diseño.

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
# En la zona del cristal (y > 750) la puerta se lleva lo MISMO que pierde la carrocería:
# ahí el parabrisas de Tripo envuelve hacia el costado y la franja |z| 0.54-0.72 es
# cristal; si se quedara sin dueño, abre un hueco junto al pilar delantero.
SECCION_PUERTA = [(Z_ESPINAZO, 1400), (2000, 1400), (2000, 150), (720, 150), (720, 690),
                  (600, 750), (450, 985), (Z_ESPINAZO, 985)]
# BISAGRA OCULTA. El eje va DENTRO del techo, 30 mm bajo la piel (el techo en el
# espinazo está a 1100-1110 entre x 1.70 y 2.10 m), así el filamento queda tapado.
# Puerta y carrocería se reparten un cilindro de radio R_NUDILLO alrededor del eje en
# tramos alternados (carrocería-puerta-carrocería): cada tramo gira dentro de su propio
# cilindro, y la piel de la puerta que queda fuera de él, al girar, sube por encima del
# techo antes de cruzar al otro lado. El ángulo libre es 180 - 2·asin(h/R), con h la
# altura de la piel sobre el eje: en el centro del techo h = 40 mm (1110), así que con
# R = 48 mm se abre hasta ~67° sin choque (verificado con choques()). Por fuera sólo se
# ven las juntas, a ~1.3 mm del espinazo a 1:20.
Y_BISAGRA = 1060.0
R_NUDILLO = 60.0                # h máx = 1110 - 1060 = 50 -> 180 - 2·asin(50/60) = 67°
R_NUCLEO = 40.0                 # mitad de abajo maciza del nudillo (cuelga en la cabina)
# tramos a lo largo de x; la parte de techo de la puerta es exactamente [1600, 2080]
NUDILLOS_CARROCERIA = [(1600, 1795), (1985, 2080)]
NUDILLO_PUERTA = (1805, 1975)
X_ENTRADA_PASADOR = 1560.0      # el eje sale a la piel justo detrás de la cabecera
ANGULO_MAX = 60.0
# la parte de techo de la puerta (por dentro de |z| = 470) sólo entre estas x: con el
# contorno inclinado del pilar, la puerta se llevaba un pedazo de la cabecera del
# parabrisas por dentro que al abrir chocaba con el resto de la cabecera
X_TECHO_PUERTA = (1600.0, 2080.0)
Z_TECHO = 470.0                 # por dentro de este |z| la puerta es "techo"

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


def _chaikin(pts, veces=3):
    """Redondea un contorno cerrado cortando esquinas: con los 12 puntos trazados, la
    curva trasera de la puerta salía en tramos rectos en el marco de la carrocería."""
    p = np.asarray(pts, float)
    for _ in range(veces):
        q = np.roll(p, -1, axis=0)
        p = np.vstack([np.column_stack([0.75 * p[:, 0] + 0.25 * q[:, 0], 0.75 * p[:, 1] + 0.25 * q[:, 1]]),
                       np.column_stack([0.25 * p[:, 0] + 0.75 * q[:, 0], 0.25 * p[:, 1] + 0.75 * q[:, 1]])])
        n = len(p) // 2
        p = np.array([p[i // 2 + (i % 2) * n] for i in range(2 * n)])
    return p.tolist()


def prisma_puerta(lado, crece, seccion=None):
    """Volumen que ocupa la puerta (crece > 0: más grande, para cortar la carrocería;
    crece < 0: más chico, para la puerta). Prisma del contorno de lado ∩ prisma de la
    sección, espejado para el lado izquierdo."""
    a = mf.CrossSection([_ccw(_chaikin(CONTORNO_LADO))]).offset(crece, mf.JoinType.Round)
    lat = mf.Manifold.extrude(a, 4000.0).translate([0, 0, -2000.0])          # (x, y) a lo largo de z
    b = mf.CrossSection([_ccw(seccion or SECCION)]).offset(crece, mf.JoinType.Round)
    sec = mf.Manifold.extrude(b, 6000.0).translate([0, 0, -1000.0])          # (z, y) a lo largo de "x"
    sec = sec.transform(np.array([[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0]], float))  # -> (x, y, z)
    P = lat ^ sec
    return P if lado > 0 else P.mirror([0, 0, 1])


def cilindro_x(x0, x1, r, y, z, n=48):
    return mf.Manifold.cylinder(x1 - x0, r, r, n).transform(
        np.array([[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0]], float)).translate([x0, y, z])


def region_puerta(lado, o, seccion):
    """Volumen de la puerta crecido `o` mm (o < 0: encogido). Costado: |z| > Z_TECHO.
    Techo: sólo entre X_TECHO_PUERTA. La carrocería se corta con o = +g y la puerta con
    o = -g, así que entre las dos sólo queda la holgura: nada de huecos."""
    x0, x1 = X_TECHO_PUERTA
    # el techo traslapa 100 mm con el costado: si sólo topan en Z_TECHO, al encoger la
    # puerta quedan separados por la holgura y la puerta pierde su pedazo de techo
    techo = mf.Manifold.cube([x1 - x0 + 2 * o, 3000, 2 * Z_TECHO + 200]).translate([x0 - o, -1000, -Z_TECHO - 100])
    costado = mf.Manifold.cube([6000, 4000, 2000]).translate([-1000, -1000, Z_TECHO - o])
    if lado < 0:
        costado = costado.mirror([0, 0, 1])
    return prisma_puerta(lado, o, seccion) ^ (techo + costado)


def puertas_gaviota(cuerpo, esc, holgura_mm=HOLGURA_MM, comp_mm=0.0):
    g = holgura_mm * esc / 2
    R = R_NUDILLO
    (b1a, b1b), (b2a, b2b) = NUDILLOS_CARROCERIA
    d0, d1 = NUDILLO_PUERTA
    puertas = []
    for lado in (1, -1):
        zb = lado * Z_ESPINAZO

        def cil(x0, x1, r):
            return cilindro_x(x0, x1, r, Y_BISAGRA, zb, 96)

        def nucleo(x0, x1):
            c = cil(x0, x1, R_NUCLEO)
            abajo = mf.Manifold.cube([4000, 4000, 4000]).translate([-1000, Y_BISAGRA - 4000, -2000])
            return c ^ abajo

        # PUERTA: su región menos los tramos de la carrocería (con holgura), más su tramo
        # de cilindro completo (también del lado del espinazo)
        r_p = region_puerta(lado, -g, SECCION_PUERTA) - cil(b1a - 50, b1b + g, R + g)             - cil(b2a - g, b2b + 50, R + g)
        puerta = (cuerpo ^ (r_p + cil(d0, d1, R - g))) + nucleo(d0, d1)
        # CARROCERÍA: pierde la región de la puerta (crecida) y el cilindro entre sus dos
        # tramos (hueco + tramo de la puerta + hueco); conserva sus tramos de cilindro
        r_c = (region_puerta(lado, +g, SECCION) - cil(b1a - 50, b1b, R - g) - cil(b2a, b2b + 50, R - g))             + cil(b1b, b2a, R + g)
        resto = (cuerpo - r_c) + nucleo(b1a, b1b) + nucleo(b2a, b2b)
        # pasador: fijo en la carrocería, libre en la puerta
        resto = resto - cil(X_ENTRADA_PASADOR, b2b - 2 * esc, (PASADOR_FIJO_MM + comp_mm) * esc / 2)
        puerta = puerta - cil(d0 - 10, d1 + 10, (PASADOR_LIBRE_MM + comp_mm) * esc / 2)
        cuerpo = resto
        puerta = max(puerta.decompose(), key=lambda p: p.volume())
        puertas.append((lado, puerta))
    return cuerpo, puertas


def choques(cuerpo, puertas, angulos=(15, 30, 45, 60, 65)):
    """Volumen (mm3 reales) que cada puerta, girada sobre su bisagra, mete en la carrocería."""
    out = {}
    for lado, p in puertas:
        zb = lado * Z_ESPINAZO
        for a in angulos:
            r = p.translate([0, -Y_BISAGRA, -zb]).rotate([-a * lado, 0, 0]).translate([0, Y_BISAGRA, zb])
            out[(lado, a)] = (r ^ cuerpo).volume()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--escala", type=int, default=20)
    ap.add_argument("--impresora", default=None)
    a = ap.parse_args()
    esc, impresora = a.escala, a.impresora      # `a` se reusa abajo en el lazo de choques
    import maqueta as Q
    from impresora import cargar as perfil_de, util_mm
    pf = perfil_de(impresora)
    Q.SALIDA, Q.CAMA_MM = pf["salida"], float(pf["cama_mm"][0])
    Q.MARGEN_MM = float(pf["cama_mm"][0]) - util_mm(pf)
    comp = pf["compensa_agujero_mm"]
    holgura = pf["holgura_puerta_mm"] or HOLGURA_MM
    print(f"impresora: {pf['nombre']}  (holgura puerta {holgura} mm, agujeros +{comp} mm, "
          f"pieza máx. {util_mm(pf):.0f} mm con brim {pf['brim_mm']} mm)")
    k = 1.0 / esc
    tm = trimesh.load(SOLIDO)
    tm = max(tm.split(only_watertight=False), key=lambda p: p.volume)
    M = a_manifold(tm)
    from tripo_juguete import cerrar_aberturas
    M, n = cerrar_aberturas(M, lamina=CRISTAL_MM * esc)
    print(f"cristal: lámina de {CRISTAL_MM} mm a escala en {n} cortes; cabina hueca con el interior de Tripo")
    cuerpo, ruedas = ruedas_que_giran(M, esc, eje_mm=2.1 + comp, cubo_mm=1.85 + comp)
    cuerpo, puertas = puertas_gaviota(cuerpo, esc, holgura, comp)
    cuerpo = max(cuerpo.decompose(), key=lambda p: p.volume())
    for (lado, a), v in choques(cuerpo, puertas).items():
        print(f"   puerta {'der' if lado > 0 else 'izq'} abierta {a:>4.0f}°: choque {v/1e3:8.1f} cm3 reales")

    ens = os.path.join(RAIZ, "cad", f"_gaviota-1a{esc}" + (f"-{impresora}" if impresora else ""))
    os.makedirs(ens, exist_ok=True)

    def en_su_lugar(m, nom):
        a_trimesh(m.scale([k, k, k])).export(os.path.join(ens, nom))

    en_su_lugar(cuerpo, "carroceria.stl")
    for lado, p in puertas:
        en_su_lugar(p, f"puerta-{'der' if lado > 0 else 'izq'}.stl")
    for i, (x, lado, r) in enumerate(ruedas):
        en_su_lugar(r, f"rueda-{i}.stl")
    json.dump({"escala": esc, "angulo_max": ANGULO_MAX,
               "bisagra": {"y": Y_BISAGRA, "z": Z_ESPINAZO,
                           "x": [X_ENTRADA_PASADOR, NUDILLOS_CARROCERIA[1][1] - 2 * esc]},
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
    if impresora:
        # placa 2: puertas y ruedas juntas, separadas lo bastante para que no se junten
        # los brims (2·brim + 4 mm)
        sep = 2 * pf["brim_mm"] + 4
        placa, x = mf.Manifold(), 0.0
        for nom, p in piezas[1:]:
            lo = p.bounding_box()
            placa = placa + p.translate([x - lo[0], -(lo[1] + lo[4]) / 2, 0])
            x += lo[3] - lo[0] + sep
        lo = placa.bounding_box()
        placa = placa.translate([-(lo[0] + lo[3]) / 2, 0, 0])
        piezas = [(f"gaviota-1a{esc}-placa1-carroceria.stl", piezas[0][1]),
                  (f"gaviota-1a{esc}-placa2-puertas-y-ruedas.stl", placa)]
    for nom, p in piezas:
        cabe, _ = reporte(nom, p)
        guardar(p, nom)
        if not cabe:
            print(f"   ! {nom} no cabe con el brim: separar las piezas en dos placas")
    largo_pasador = (NUDILLOS_CARROCERIA[1][1] - 2 * esc - X_ENTRADA_PASADOR) * k
    print(f"   pasadores de bisagra: 2 tramos de filamento 1.75 de {largo_pasador:.0f} mm, "
          f"entran por un agujerito en la cabecera del parabrisas (luego una gota de pintura)")
    print(f"   ejes de rueda: 2 tramos de {2 * Z_EXT * k - 1:.0f} mm")


if __name__ == "__main__":
    main()
