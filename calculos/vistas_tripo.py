# -*- coding: utf-8 -*-
"""
Las 4 vistas de la lámina a UNA sola escala, para multiview_to_model de Tripo.

Las vistas de ref/gemini/ vienen cada una estirada a 931 px de ancho, sea frente o
lado: el frente sale tan "grande" como el costado y Tripo recibiría un carro de
proporciones imposibles. Aquí se lleva cada vista a la misma escala usando la ÚNICA
cota que comparten las cuatro: la altura del piso (base de las llantas) al techo.
El piso queda en la misma fila en las cuatro y cada carro centrado. No se deforma
nada: sólo escala uniforme, recorte de la sombra y traslación.

Salida: ref/tripo/multivista/{front,left,back,right}.png  +  hoja.png (revisión)
    python calculos/vistas_tripo.py [--lienzo 1024] [--largo 0.92]
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(HERE, "..")
GEM = os.path.join(RAIZ, "ref", "gemini")
SAL = os.path.join(RAIZ, "ref", "tripo", "multivista")

# vista de Tripo -> imagen de la lámina. Convención de Tripo (relativa al que mira, no
# al objeto): "left" = la nariz apunta a la IZQUIERDA de la imagen, que es
# ia-lateral.png. "right" es esa misma lateral en espejo (el carro es simétrico; la
# lámina sólo dibujó un costado).
VISTAS = {"front": "ia-frontal.png", "left": "ia-lateral.png",
          "back": "ia-trasera.png", "right": "ia-lateral-espejo.png"}


def caja_sin_sombra(im):
    """Caja del carro sin la sombra del piso. La sombra de la lámina es opaca, pero
    clara: el piso es la última fila con pixeles oscuros (llantas)."""
    a = np.asarray(im).astype(float)
    alfa, lum = a[:, :, 3], a[:, :, :3].mean(2)
    opaco = alfa > 200
    oscuro = (opaco & (lum < 45)).sum(1)
    filas = np.where(opaco.any(1))[0]
    piso = int(np.where(oscuro > 0.02 * opaco.shape[1])[0].max())
    cols = np.where(opaco[: piso + 1].any(0))[0]
    return int(cols.min()), int(filas.min()), int(cols.max()), piso


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lienzo", type=int, default=1024)
    ap.add_argument("--largo", type=float, default=0.92,
                    help="fracción del lienzo que ocupa el LARGO en las laterales")
    a = ap.parse_args()
    os.makedirs(SAL, exist_ok=True)

    cajas = {v: caja_sin_sombra(Image.open(os.path.join(GEM, f)).convert("RGBA"))
             for v, f in VISTAS.items()}
    # escala común: la lateral ocupa `largo` del lienzo; su altura en px es la regla
    x0, y0, x1, y1 = cajas["left"]
    k_lat = a.largo * a.lienzo / (x1 - x0)
    alto_px = (y1 - y0) * k_lat
    piso_px = int(a.lienzo / 2 + alto_px / 2)
    datos = {}
    for v, f in VISTAS.items():
        im = Image.open(os.path.join(GEM, f)).convert("RGBA")
        x0, y0, x1, y1 = cajas[v]
        recorte = im.crop((x0, y0, x1 + 1, y1 + 1))          # fuera la sombra
        k = alto_px / (y1 - y0)
        w, h = round((x1 - x0 + 1) * k), round((y1 - y0 + 1) * k)
        recorte = recorte.resize((w, h), Image.LANCZOS)
        lienzo = Image.new("RGBA", (a.lienzo, a.lienzo), (255, 255, 255, 255))
        lienzo.alpha_composite(recorte, ((a.lienzo - w) // 2, piso_px - h))
        lienzo.convert("RGB").save(os.path.join(SAL, f"{v}.png"))
        datos[v] = {"fuente": f, "caja_px": [x0, y0, x1, y1], "escala": round(k, 4),
                    "ancho_px": w, "alto_px": h, "ancho_sobre_alto": round(w / h, 3)}
    json.dump({"lienzo": a.lienzo, "piso_px": piso_px, "vistas": datos},
              open(os.path.join(SAL, "escala.json"), "w", encoding="utf-8"), indent=1)

    # hoja de revisión: las 4 con la línea de piso y la de techo comunes
    hoja = Image.new("RGB", (a.lienzo * 4 // 2, a.lienzo // 2), "white")
    for i, v in enumerate(("front", "left", "back", "right")):
        im = Image.open(os.path.join(SAL, f"{v}.png")).resize((a.lienzo // 2, a.lienzo // 2))
        hoja.paste(im, (i * a.lienzo // 2, 0))
    d = ImageDraw.Draw(hoja)
    for y in (piso_px // 2, (piso_px - alto_px) // 2):
        d.line([(0, y), (hoja.width, y)], fill=(220, 40, 40), width=1)
    hoja.save(os.path.join(SAL, "hoja.png"))

    print(f"escala común: altura del carro = {alto_px:.0f} px, piso en y = {piso_px}")
    for v, dd in datos.items():
        print(f"   {v:6s} {dd['ancho_px']:4d} x {dd['alto_px']:3d} px   ancho/alto {dd['ancho_sobre_alto']:.2f}"
              f"   (de {dd['fuente']}, x{dd['escala']:.3f})")
    lat, fr = datos["left"], datos["front"]
    print(f"   proporción que recibe Tripo: largo {lat['ancho_sobre_alto']:.2f} : ancho "
          f"{fr['ancho_sobre_alto']:.2f} : alto 1   (el paquete actual: 3.19 : 1.65 : 1)")


if __name__ == "__main__":
    main()
