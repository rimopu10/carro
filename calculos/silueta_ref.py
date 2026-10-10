# -*- coding: utf-8 -*-
"""
Extrae la silueta de la imagen de referencia del dueño y la deja normalizada.

Por qué: teclear a ojo la curva del techo nunca va a dar el carro de la foto. Lo que
sí da es medirla. Se recorta la vista lateral de la lámina, se separa el carro del
fondo, se sacan el perfil superior y el inferior columna por columna, se localizan
los dos ejes por sus ruedas y se normaliza TODO por la distancia entre ejes. Así la
forma queda independiente del tamaño del concepto y se puede montar sobre nuestra
batalla de 2.13 m.

La lámina es un render, no un plano: el resultado es la INTENCIÓN de la silueta, no
una cota. Por eso después se recorta contra la envolvente real del chasis.

Correr:  python calculos/silueta_ref.py
Salidas: ref/silueta-referencia.json   perfiles normalizados
         ref/silueta-verificacion.png  qué se midió exactamente
"""
import json
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "ref")

# Recorte de la vista lateral dentro de la lámina, en fracción de la imagen.
CAJA = (0.500, 0.050, 0.902, 0.318)   # sin la vista cenital ni el rótulo
UMBRAL = 198          # la cuadrícula del fondo ronda 210-230: por debajo de
                      # 198 solo queda el carro
MIN_RUN = 6           # px seguidos: descarta las líneas finas de la cuadrícula


def cargar():
    im = Image.open(os.path.join(REF, "ref-lamina.jpg")).convert("L")
    W, H = im.size
    x0, y0, x1, y1 = (int(CAJA[0] * W), int(CAJA[1] * H),
                      int(CAJA[2] * W), int(CAJA[3] * H))
    return np.asarray(im.crop((x0, y0, x1, y1)), dtype=np.int16)


def perfiles(g):
    """Para cada columna, primer y último pixel de carro, ignorando la cuadrícula."""
    oscuro = g < UMBRAL
    alto, ancho = oscuro.shape
    sup = np.full(ancho, -1)
    inf = np.full(ancho, -1)
    for c in range(ancho):
        col = oscuro[:, c]
        if not col.any():
            continue
        # se exige una racha continua para no morder una línea de la cuadrícula
        run = 0
        for r in range(alto):
            run = run + 1 if col[r] else 0
            if run >= MIN_RUN:
                sup[c] = r - run + 1
                break
        run = 0
        for r in range(alto - 1, -1, -1):
            run = run + 1 if col[r] else 0
            if run >= MIN_RUN:
                inf[c] = r + run - 1
                break
    return sup, inf


def recortar_al_carro(sup, inf):
    """Se queda con el tramo continuo más largo: descarta el texto y la vista cenital
    que comparten la banda."""
    val = (sup >= 0) & (inf > sup) & ((inf - sup) > 25)
    mejor, ini, largo = (0, 0), None, 0
    for c, v in enumerate(val):
        if v and ini is None:
            ini = c
        elif not v and ini is not None:
            if c - ini > largo:
                largo, mejor = c - ini, (ini, c)
            ini = None
    if ini is not None and len(val) - ini > largo:
        mejor = (ini, len(val))
    return mejor


# Puntos de referencia LEÍDOS sobre el recorte con rejilla (ref/_rejilla.png), en px.
# Se hicieron a mano a propósito: detectarlos automáticamente falla porque la lámina
# lleva una sombra de piso continua bajo todo el carro y una cuadrícula de fondo, y
# no vale la pena un detector frágil para medir una sola imagen fija.
EJE_DEL_PX, EJE_TRAS_PX = 122, 483
SUELO_PX = 220
MORRO_PX, COLA_PX = 6, 580


def main():
    g = cargar()
    sup, inf = perfiles(g)
    a, b = MORRO_PX, COLA_PX
    s = sup[a:b].astype(float)
    i = inf[a:b].astype(float)
    # huecos (columnas sin carro): se rellenan por interpolación
    for arr in (s, i):
        malo = arr < 0
        if malo.any():
            arr[malo] = np.interp(np.flatnonzero(malo), np.flatnonzero(~malo), arr[~malo])
    suelo = float(SUELO_PX)
    ex1 = EJE_DEL_PX - a
    batalla_px = float(EJE_TRAS_PX - EJE_DEL_PX)

    # normalización: origen en el eje delantero, unidad = distancia entre ejes,
    # Y hacia arriba desde el suelo
    xs = (np.arange(len(s)) - ex1) / batalla_px
    techo = (suelo - s) / batalla_px
    piso = np.clip((suelo - i) / batalla_px, 0.0, None)
    largo_norm = (len(s) - 1) / batalla_px
    alto_norm = float(techo.max())

    datos = {
        "x": [round(float(v), 5) for v in xs],
        "techo": [round(float(v), 5) for v in techo],
        "piso": [round(float(v), 5) for v in piso],
        "eje_del": 0.0,
        "eje_tras": 1.0,
        "voladizo_del": round(float(-xs[0]), 4),
        "voladizo_tras": round(float(xs[-1] - 1.0), 4),
        "largo_sobre_batalla": round(largo_norm, 4),
        "alto_sobre_batalla": round(alto_norm, 4),
        "rueda_radio_sobre_batalla": round(48.0 / batalla_px, 4),
    }
    os.makedirs(REF, exist_ok=True)
    with open(os.path.join(REF, "silueta-referencia.json"), "w", encoding="utf-8") as f:
        json.dump(datos, f, separators=(",", ":"))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(15, 5.2), facecolor="#0d1117")
    ax.set_facecolor("#0d1117")
    ax.imshow(g[:, a:b], cmap="gray", aspect="equal")
    ax.plot(s, color="#58a6ff", lw=2.0, label="perfil superior medido")
    ax.plot(i, color="#f0a868", lw=2.0, label="perfil inferior medido")
    ax.axhline(suelo, color="#3fb950", lw=1.2, ls="--", label="suelo")
    for e, nom in ((ex1, "eje del."), (ex1 + batalla_px, "eje tras.")):
        ax.axvline(e, color="#f85149", lw=1.2)
        ax.text(e, 8, nom, color="#f85149", fontsize=9, ha="center")
    ax.legend(loc="lower left", fontsize=9, facecolor="#161b22", labelcolor="#c9d1d9")
    ax.set_title(f"Silueta medida de la referencia · batalla {batalla_px} px · "
                 f"largo/batalla {largo_norm:.3f} · alto/batalla {alto_norm:.3f}",
                 color="#c9d1d9", fontsize=11)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(os.path.join(REF, "silueta-verificacion.png"), dpi=110,
                facecolor="#0d1117")

    print(f"OK  ancho util {b-a} px · batalla {batalla_px} px")
    print(f"    largo/batalla   {largo_norm:.3f}")
    print(f"    alto/batalla    {alto_norm:.3f}")
    print(f"    voladizo del.   {datos['voladizo_del']:.3f} batallas")
    print(f"    voladizo tras.  {datos['voladizo_tras']:.3f} batallas")
    print(f"OK  {os.path.normpath(os.path.join(REF, 'silueta-referencia.json'))}")


if __name__ == "__main__":
    main()
