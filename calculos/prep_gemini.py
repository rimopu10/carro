# -*- coding: utf-8 -*-
"""
Prepara las vistas nuevas para el reconstructor 3D.

Se usa el removedor de fondo del propio Hunyuan (rembg) y no un umbral casero: las
láminas traen sombra difusa bajo el carro y un umbral simple se la come como si fuera
carrocería — que es de donde salían el pedestal y el panel plano.

Después cada vista se recorta a su silueta, se centra en lienzo cuadrado con margen y
se deja a 1024 px, que es lo que estos modelos esperan.

    "C:/AI/HY3D/Hunyuan3D2_WinPortable/python_standalone/python.exe" -s -u \
        calculos/prep_gemini.py
"""
import os

import numpy as np
from PIL import Image
from scipy import ndimage

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEM = os.path.join(RAIZ, "ref", "gemini")

# qué es cada archivo, leído de la hoja de contacto
VISTAS = {"g1": "trasera", "g2": "lateral", "g3": "frontal",
          "g4": "cenital", "g5": "tres_cuartos"}
LADO = 1024


def quitar_fondo(im, umbral=172):
    """Fondo = lo claro CONECTADO AL BORDE de la imagen.

    Un umbral simple sobre el brillo se traga la sombra difusa bajo el carro y la
    convierte en geometría — de ahí salían el pedestal y el panel plano. Inundando
    desde los bordes sólo se marca como fondo lo que de verdad rodea a la pieza.
    """
    g = np.asarray(im.convert("L"), dtype=np.int16)
    claro = g > umbral
    etiq, n = ndimage.label(claro)
    del_borde = set(etiq[0, :]) | set(etiq[-1, :]) | set(etiq[:, 0]) | set(etiq[:, -1])
    del_borde.discard(0)
    fondo = np.isin(etiq, list(del_borde))
    obj = ~fondo
    obj = ndimage.binary_closing(obj, np.ones((5, 5)))
    et2, n2 = ndimage.label(obj)
    if n2:
        tam = ndimage.sum(obj, et2, range(1, n2 + 1))
        obj = et2 == (int(np.argmax(tam)) + 1)
    obj = ndimage.binary_fill_holes(obj)
    obj = ndimage.binary_erosion(obj, np.ones((3, 3)), iterations=2)
    a = np.asarray(im.convert("RGB"))
    return Image.fromarray(np.dstack([a, (obj * 255).astype("uint8")]), "RGBA")


def main():
    for clave, nombre in VISTAS.items():
        f = os.path.join(GEM, f"{clave}.jpg")
        if not os.path.exists(f):
            print(f"falta {f}")
            continue
        im = Image.open(f).convert("RGB")
        rgba = quitar_fondo(im)
        a = np.asarray(rgba)[:, :, 3]
        ys, xs = np.where(a > 8)
        if len(xs) == 0:
            print(f"{nombre}: no se encontró el carro")
            continue
        rgba = rgba.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
        L = int(max(rgba.size) * 1.10)
        lienzo = Image.new("RGBA", (L, L), (255, 255, 255, 0))
        lienzo.paste(rgba, ((L - rgba.width) // 2, (L - rgba.height) // 2), rgba)
        lienzo = lienzo.resize((LADO, LADO), Image.LANCZOS)
        salida = os.path.join(GEM, f"ia-{nombre}.png")
        lienzo.save(salida)
        cob = (np.asarray(lienzo)[:, :, 3] > 8).mean()
        print(f"OK {nombre:14s} carro {rgba.size[0]}x{rgba.size[1]} px  "
              f"cobertura {cob*100:.0f}%  ->  {os.path.basename(salida)}")
    # espejo del costado, para darle los dos lados al modelo multivista
    lat = os.path.join(GEM, "ia-lateral.png")
    if os.path.exists(lat):
        Image.open(lat).transpose(Image.FLIP_LEFT_RIGHT).save(
            os.path.join(GEM, "ia-lateral-espejo.png"))
        print("OK lateral-espejo")


if __name__ == "__main__":
    main()
