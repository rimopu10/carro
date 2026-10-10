# -*- coding: utf-8 -*-
"""
Hoja ortográfica del paquete — el andamio geométrico para regenerar la referencia.

Por qué existe: las láminas de Gemini NO son consistentes entre sí. Cada vista tiene
su propio punto de fuga y sus propias proporciones, así que no hay un sólido 3D que se
proyecte exacto a todas — y encima traían la postura equivocada (voladizos invertidos,
ya corregidos en carroceria.py). Pedirle a un reconstructor que arregle eso es pedirle
que adivine. Lo que sí se puede es arreglar la ENTRADA.

Esto genera las cuatro vistas ortográficas del paquete REAL, todas al mismo metro por
píxel y sobre la misma línea de suelo, para usarlas como andamio al regenerar la hoja
de referencia. Lo que salga de ahí ya es consistente por construcción, y va a un
reconstructor multivista sabiendo que la proporción no se puede ir.

Dos salidas, y la diferencia importa:
  ref/blueprint-tecnico.png   con cotas y rótulos — para leerlo tú y verificar
  ref/blueprint-limpio.png    sin una sola letra — este es el que se le da al
                              generador; el texto en una imagen de referencia lo
                              distrae y termina dibujando las letras

Escala verdadera entre vistas: las cuatro se dibujan en UNOS SOLOS ejes con offsets,
no en subplots. Un subplot por vista deja que matplotlib escale cada uno por su cuenta
y la hoja miente justo en lo único que tiene que decir la verdad.

Correr:  python calculos/blueprint.py
"""
import os

import numpy as np

import carroceria as C


# Vistas: (nombre, dirección de cámara). Ver base_camara() en carroceria.py — para
# LAT sale u=x,v=y; CEN u=x,v=z; FRO u=z,v=y; TRA u=-z,v=y (espejada, como debe ser).
LAT, CEN, FRO, TRA = (0, 0, 1), (0, -1, 0), (-1, 0, 0), (1, 0, 0)

GAP = 0.34          # separación entre vistas, en metros de modelo


def proyectar(tris, cam, dx, dy):
    """Proyecta triángulos con la cámara y los recorre a su casilla de la hoja."""
    _, ex, ey = C.base_camara(cam)
    return [np.column_stack([np.array(t) @ ex + dx, np.array(t) @ ey + dy])
            for t in tris]


def extension(tris, cam):
    _, ex, ey = C.base_camara(cam)
    P = np.array([p for t in tris for p in t], float)
    u, v = P @ ex, P @ ey
    return u.min(), u.max(), v.min(), v.max()


def contorno_lamina():
    """Contorno lateral MEDIDO de la lámina, llevado a nuestro paquete.

    Esto es lo único honesto que puede llevar un andamio como contorno. El perfil que
    construye carroceria.py es un loft sobre 16 estaciones tecleadas a mano: sirve para
    decidir paquete —dónde caen las ruedas, si cabe el piloto, si la puerta abre— y NO
    se parece a la lámina, ni tenía por qué. Meterlo en el andamio fue un error: anclaba
    al generador a un jabón.

    Lo que sí viene medido de la imagen del dueño es el par techo/piso de
    ref/silueta-referencia.json, normalizado por batalla. Escalado a NUESTRA batalla da
    la silueta de SU carro sobre NUESTROS puntos duros — que es exactamente lo que el
    andamio tiene que decir.

    Se recorta el margen de borde: los últimos milímetros del recorte tienen el techo
    saltando a 1.05 m, más alto que la cabina, que es imposible.
    """
    x = np.array(C._SIL["x"]) * C.BATALLA + C.EJE_DEL
    techo = np.array(C._SIL["techo"]) * C.BATALLA
    piso = np.array(C._SIL["piso"]) * C.BATALLA
    ok = (x >= x.min() + C.MARGEN_REF) & (x <= x.max() - C.MARGEN_REF)
    x, techo, piso = x[ok], techo[ok], piso[ok]
    arriba = list(zip(x, techo))
    abajo = list(zip(x[::-1], piso[::-1]))
    return np.array(arriba + abajo)


NX = 240        # muy por encima de los 92 de la lámina: aquí el contorno ES el
                # entregable, y a 92 estaciones el perfil sale escalonado


def piezas(nx=NX):
    """Las mismas superficies que usa la lámina de proporciones, por material."""
    xs, anillos, n_media = C.malla(nx=nx)
    marca = C.celdas(xs, anillos, n_media)
    sup = C.superficies(xs, anillos, marca)

    def por_mat(*mats):
        return [t for (g, m), ts in sup.items() if m in mats for t in ts]

    ejes = ((C.EJE_DEL, C.R_DEL, C.Z_RUEDA_DEL), (C.EJE_TRAS, C.R_TRAS, C.Z_RUEDA_TRAS))
    return {
        "pintura": por_mat("pintura"),
        "vidrio": por_mat("vidrio"),
        "negro": por_mat("negro"),
        "luz": por_mat("luz_t", "luz_d"),
        "llanta": [t for (xa, R, zc) in ejes for lado in (+1, -1)
                   for t in C.rueda(xa, R, zc, lado)],
        "rin": [t for (xa, R, zc) in ejes for lado in (+1, -1)
                for t in C.rin(xa, R, zc, lado)],
    }


# Orden de pintado: de atrás hacia adelante. La llanta va antes que el cuerpo para que
# la salpicadera la tape, que es lo que pasa en el carro real.
CAPAS = ("llanta", "rin", "negro", "pintura", "vidrio", "luz")


def colocar(P):
    """Offsets de cada vista para que compartan escala y línea de suelo.

        LATERAL   FRONTAL
        CENITAL   TRASERA

    Lateral y cenital comparten el eje x; frontal y trasera comparten la línea de
    suelo con la lateral. Así el que mire la hoja puede seguir una cota de una vista
    a otra sin recalcular nada.
    """
    todo = [t for k in CAPAS for t in P[k]]
    lu0, lu1, lv0, lv1 = extension(todo, LAT)
    cu0, cu1, cv0, cv1 = extension(todo, CEN)
    fu0, fu1, fv0, fv1 = extension(todo, FRO)

    ancho_lat, alto_lat = lu1 - lu0, lv1 - lv0
    alto_cen = cv1 - cv0
    return {
        # lateral: en el origen, con el suelo en y=0
        "lateral": (LAT, -lu0, -lv0),
        # cenital: mismo x, debajo
        "cenital": (CEN, -cu0, -cv0 - alto_cen - GAP),
        # frontal: a la derecha, misma línea de suelo
        "frontal": (FRO, ancho_lat + GAP - fu0, -fv0),
        # trasera: a la derecha, alineada con la cenital
        "trasera": (TRA, ancho_lat + GAP - fu0, -cv0 - alto_cen - GAP),
    }, (ancho_lat, alto_lat, alto_cen)


def dibujar(ax, P, disposicion, paleta, plana=False):
    """plana=True dibuja SOLO silueta (cuerpo + rueda), sin desglose de materiales.

    Es lo correcto para el andamio: el `material()` de hoy manda todo lo que está sobre
    la cintura entre el cowl y x=2.13 a "vidrio", techo incluido, así que la cenital
    sale con un ventanal rectangular gigante que NO es una decisión tomada. Un andamio
    tiene que afirmar solo lo que ya está decidido —proporción, postura, contorno— y
    callarse el resto; si le pinta un ventanal falso al generador, el generador lo
    dibuja.
    """
    from matplotlib.collections import PolyCollection
    # En el andamio la rueda va ENCIMA del cuerpo, al revés que en un render. Un plano
    # de paquete existe para fijar dónde están los ejes y qué diámetro tienen; si la
    # salpicadera las tapa —que es lo que pasa en el carro real— el generador se queda
    # sin la única referencia dura de la hoja y vuelve a inventar la postura.
    capas = (("cuerpo", "llanta", "rin") if plana else CAPAS)
    for z, capa in enumerate(capas):
        color = paleta[capa]
        tris = (P["pintura"] + P["vidrio"] + P["negro"] + P["luz"]
                if capa == "cuerpo" else P[capa])
        for (cam, dx, dy) in disposicion.values():
            polis = proyectar(tris, cam, dx, dy)
            if not polis:
                continue
            ax.add_collection(PolyCollection(
                polis, facecolors=color, edgecolors=color, linewidths=0.5,
                antialiased=False, zorder=z + 2))


# ============================================================================
PALETA_TEC = {"pintura": "#ced5dd", "vidrio": "#5b6673", "negro": "#20262e",
              "luz": "#e8a35c", "llanta": "#20262e", "rin": "#48515c"}
# Andamio: un tono plano de cuerpo y la rueda claramente separada. Nada más — el
# contraste alto y la ausencia de detalle son la función, no una simplificación.
PALETA_LIM = {"cuerpo": "#e6eaee", "llanta": "#161a1f", "rin": "#161a1f"}


def hoja(P, limpia):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    disposicion, (ancho_lat, alto_lat, alto_cen) = colocar(P)
    fondo = "#0d1117" if not limpia else "#20262d"
    W = ancho_lat + GAP + C.ANCHO
    H = alto_lat + GAP + alto_cen

    fig = plt.figure(figsize=(15.0, 15.0 * (H + 0.9) / (W + 0.5)), facecolor=fondo)
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
    ax.set_facecolor(fondo)
    dibujar(ax, P, disposicion, PALETA_TEC if not limpia else PALETA_LIM,
            plana=limpia)

    if not limpia:
        _cotas(ax, disposicion, ancho_lat, alto_lat, alto_cen)

    ax.set_xlim(-0.25, W + 0.25)
    ax.set_ylim(-(alto_cen + GAP) - 0.45, alto_lat + (0.45 if not limpia else 0.15))
    ax.set_aspect("equal")
    ax.axis("off")

    nombre = "blueprint-limpio.png" if limpia else "blueprint-tecnico.png"
    out = os.path.join(C.HERE, "..", "ref", nombre)
    fig.savefig(out, dpi=150, facecolor=fondo)
    plt.close(fig)
    return os.path.normpath(out)


def _cotas(ax, disposicion, ancho_lat, alto_lat, alto_cen):
    """Solo en la hoja técnica. La limpia no lleva ni una letra, a propósito."""
    _, dx, dy = disposicion["lateral"]
    x0, x1 = C.X_MORRO + dx, C.X_COLA + dx
    ed, et = C.EJE_DEL + dx, C.EJE_TRAS + dx
    ax.plot([x0 - 0.1, x1 + 0.1], [0, 0], color=C.C_COTA, lw=1.0, zorder=1)
    C.cota_h(ax, x0, x1, -0.30, f"largo {C.LARGO:.3f} m")
    C.cota_h(ax, ed, et, -0.19, f"batalla {C.BATALLA:.3f} m")
    C.cota_h(ax, x0, ed, -0.085, f"voladizo {C.VOL_DEL*1000:.0f}")
    C.cota_h(ax, et, x1, -0.085, f"voladizo {C.VOL_TRAS*1000:.0f}")
    C.cota_v(ax, x1 + 0.20, 0, C.ALTO, f"alto {C.ALTO:.3f} m")

    _, fdx, fdy = disposicion["frontal"]
    C.cota_h(ax, fdx - C.SEMI, fdx + C.SEMI, -0.19, f"ancho {C.ANCHO:.3f} m")

    for etq, clave, yoff in (("LATERAL", "lateral", alto_lat + 0.10),
                             ("FRONTAL", "frontal", alto_lat + 0.10),
                             ("CENITAL", "cenital", -GAP - 0.16),
                             ("TRASERA", "trasera", -GAP - 0.16)):
        _, ddx, _ = disposicion[clave]
        ax.text(ddx if clave in ("frontal", "trasera") else ddx + C.X_MORRO + 0.02,
                yoff, etq, color=C.TENUE, fontsize=11, fontweight="bold",
                ha="center" if clave in ("frontal", "trasera") else "left", zorder=9)

    ax.text(C.X_MORRO + 0.02, alto_lat + 0.32,
            f"PAQUETE REAL — {C.LARGO:.2f} x {C.ANCHO:.2f} x {C.ALTO:.2f} m  ·  "
            f"voladizos corregidos contra ref/silueta-referencia.json  ·  "
            f"batalla y trocha SIN TOCAR",
            color="#f0f6fc", fontsize=12, fontweight="bold", zorder=9)


def hoja_andamio(P):
    """El andamio de verdad: contorno MEDIDO de la lámina + puntos duros. Nada más.

    Regla: la hoja solo afirma lo que ya está decidido. El contorno lateral es el de la
    lámina del dueño (medido, no interpretado); las ruedas, la batalla, la trocha y la
    caja envolvente son puntos duros del paquete. La FORMA de la carrocería en planta y
    de frente NO está decidida —es justo lo que se le está pidiendo al generador— así
    que ahí se dibuja la caja envolvente y se calla. Una hoja que inventa contorno
    ancla al generador a la invención.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection

    CUERPO, RUEDA, CAJA = "#e6eaee", "#161a1f", "#767f8a"
    fondo = "#20262d"
    cont = contorno_lamina()
    largo = cont[:, 0].max() - cont[:, 0].min()
    x0 = cont[:, 0].min()

    # lateral arriba; cenital abajo compartiendo x; frontal a la derecha
    off = {"lateral": (0.0, 0.0),
           "cenital": (0.0, -(C.ANCHO + GAP)),
           "frontal": (largo + GAP + C.SEMI - x0, 0.0)}

    fig = plt.figure(figsize=(15.0, 15.0 * (C.ALTO + C.ANCHO + 2 * GAP) /
                              (largo + C.ANCHO + 2 * GAP)), facecolor=fondo)
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
    ax.set_facecolor(fondo)

    # ---- LATERAL: el contorno de la lámina, tal cual se midió --------------------
    dx, dy = off["lateral"]
    ax.fill(cont[:, 0] + dx, cont[:, 1] + dy, color=CUERPO, zorder=2)
    for (xa, R, zc) in ((C.EJE_DEL, C.R_DEL, C.Z_RUEDA_DEL),
                        (C.EJE_TRAS, C.R_TRAS, C.Z_RUEDA_TRAS)):
        a = np.linspace(0, 2 * np.pi, 96)
        ax.fill(xa + R * np.cos(a) + dx, R + R * np.sin(a) + dy, color=RUEDA, zorder=3)

    # ---- CENITAL y FRONTAL: solo caja envolvente y ruedas ------------------------
    dx, dy = off["cenital"]
    ax.plot([x0 + dx, x0 + largo + dx, x0 + largo + dx, x0 + dx, x0 + dx],
            [dy - C.SEMI, dy - C.SEMI, dy + C.SEMI, dy + C.SEMI, dy - C.SEMI],
            color=CAJA, lw=2.0, ls=(0, (7, 5)), zorder=2)
    for (xa, R, zc) in ((C.EJE_DEL, C.R_DEL, C.Z_RUEDA_DEL),
                        (C.EJE_TRAS, C.R_TRAS, C.Z_RUEDA_TRAS)):
        for lado in (+1, -1):
            ax.fill([xa - R + dx, xa + R + dx, xa + R + dx, xa - R + dx],
                    [dy + lado * zc - C.ANCHO_LL / 2, dy + lado * zc - C.ANCHO_LL / 2,
                     dy + lado * zc + C.ANCHO_LL / 2, dy + lado * zc + C.ANCHO_LL / 2],
                    color=RUEDA, zorder=3)

    dx, dy = off["frontal"]
    ax.plot([dx - C.SEMI, dx + C.SEMI, dx + C.SEMI, dx - C.SEMI, dx - C.SEMI],
            [dy, dy, dy + C.ALTO, dy + C.ALTO, dy], color=CAJA, lw=2.0,
            ls=(0, (7, 5)), zorder=2)
    for lado in (+1, -1):
        z = lado * C.Z_RUEDA_DEL
        ax.fill([dx + z - C.ANCHO_LL / 2, dx + z + C.ANCHO_LL / 2,
                 dx + z + C.ANCHO_LL / 2, dx + z - C.ANCHO_LL / 2],
                [dy, dy, dy + 2 * C.R_DEL, dy + 2 * C.R_DEL], color=RUEDA, zorder=3)

    ax.set_xlim(x0 - 0.25, x0 + largo + GAP + C.ANCHO + 0.25)
    ax.set_ylim(-(C.ANCHO + GAP) - C.SEMI - 0.25, C.ALTO + 0.25)
    ax.set_aspect("equal")
    ax.axis("off")
    out = os.path.join(C.HERE, "..", "ref", "blueprint-andamio.png")
    fig.savefig(out, dpi=150, facecolor=fondo)
    plt.close(fig)
    return os.path.normpath(out)


def main():
    P = piezas()
    a = hoja(P, limpia=False)
    b = hoja(P, limpia=True)
    c = hoja_andamio(P)
    print(f"OK  {c}   <- ANDAMIO: contorno medido de la lamina + puntos duros")
    print(f"OK  {a}")
    print(f"OK  {b}   <- esta es la que se le da al generador (sin texto)")
    print(f"    4 vistas ortograficas a la MISMA escala, suelo compartido")
    print(f"    {C.LARGO:.3f} x {C.ANCHO:.3f} x {C.ALTO:.3f} m  ·  "
          f"batalla {C.BATALLA:.3f}  ·  voladizos {C.VOL_DEL*1000:.0f}/"
          f"{C.VOL_TRAS*1000:.0f} mm")


if __name__ == "__main__":
    main()
