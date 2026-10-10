# -*- coding: utf-8 -*-
"""
Compara el modelo v3 contra la referencia, vista por vista y con número.

Para cada vista ortográfica (frontal, trasera, lateral, cenital) toma la referencia
(ref/gemini/ia-*.png, fondo transparente) y el render del modelo (render/salida/v3/,
también con fondo transparente), saca la silueta de cada una por el canal alfa, las
lleva a la misma caja (la referencia está estirada distinto en cada vista, así que se
normaliza por caja y no por escala) y mide el IoU: área común / área total. 1.00 sería
la misma silueta; un carro real fotografiado dos veces da ~0.97.

Salidas:
  render/salida/v3/comparacion.png   referencia y modelo lado a lado + IoU
  render/salida/v3/siluetas.png      las dos siluetas superpuestas (rojo = sólo
                                     referencia, azul = sólo modelo)
Correr:  python render/comparar_v3.py
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(RAIZ, "ref", "gemini")
SAL = os.path.join(RAIZ, "render", "salida", "v3")
VISTAS = ["frontal", "trasera", "lateral", "cenital"]
FONDO = (20, 22, 27)


def mascara(ruta, umbral=200):
    im = Image.open(ruta).convert("RGBA")
    a = np.asarray(im)[..., 3]
    return a >= umbral, im


def recorte(m):
    ys, xs = np.where(m)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def normalizar(m, caja, tam=(600, 400)):
    x0, y0, x1, y1 = caja
    sub = Image.fromarray((m[y0:y1, x0:x1] * 255).astype(np.uint8))
    return np.asarray(sub.resize(tam, Image.BILINEAR)) > 127


def iou(a, b):
    return float((a & b).sum()) / float((a | b).sum())


def sobre_fondo(im, tam):
    """Compone la imagen RGBA sobre el fondo oscuro, recortada a su contenido."""
    m, _ = (np.asarray(im)[..., 3] >= 8), None
    x0, y0, x1, y1 = recorte(m)
    im = im.crop((x0, y0, x1, y1))
    esc = min(tam[0] / im.width, tam[1] / im.height)
    im = im.resize((int(im.width * esc), int(im.height * esc)), Image.LANCZOS)
    fondo = Image.new("RGBA", tam, (*FONDO, 255))
    fondo.alpha_composite(im, ((tam[0] - im.width) // 2, (tam[1] - im.height) // 2))
    return fondo.convert("RGB")


def main():
    try:
        fuente = ImageFont.truetype("arial.ttf", 22)
        chica = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        fuente = chica = ImageFont.load_default()
    W, H = 560, 400
    hoja = Image.new("RGB", (4 * W + 50, 2 * H + 110), FONDO)
    sil = Image.new("RGB", (4 * 600 + 50, 400 + 90), FONDO)
    d = ImageDraw.Draw(hoja)
    ds = ImageDraw.Draw(sil)
    resumen = []
    for i, v in enumerate(VISTAS):
        mr, imr = mascara(os.path.join(REF, f"ia-{v}.png"))
        mm, imm = mascara(os.path.join(SAL, f"{v}.png"))
        # la cenital de la referencia mira con la nariz a la izquierda; el render
        # también (cámara desde +y con la x del carro a la derecha... se verifica por
        # el lado donde está la punta: la referencia tiene el morro a la izquierda)
        a = normalizar(mr, recorte(mr))
        b = normalizar(mm, recorte(mm))
        # si la orientación horizontal está espejada, se prueba la volteada
        j1, j2 = iou(a, b), iou(a, b[:, ::-1])
        if j2 > j1:
            b = b[:, ::-1]
            imm = imm.transpose(Image.FLIP_LEFT_RIGHT)
            mm = mm[:, ::-1]
        j = max(j1, j2)
        resumen.append((v, j))
        x = 10 + i * (W + 10)
        hoja.paste(sobre_fondo(imr, (W, H)), (x, 50))
        hoja.paste(sobre_fondo(imm, (W, H)), (x, 50 + H + 10))
        d.text((x, 12), f"{v.upper()}   IoU {j:.3f}", fill=(240, 246, 252), font=fuente)
        d.text((x, 50 + H - 24), "referencia", fill=(125, 133, 144), font=chica)
        d.text((x, 50 + 2 * H - 14), "modelo v3", fill=(125, 133, 144), font=chica)
        # siluetas superpuestas
        rgb = np.zeros((400, 600, 3), np.uint8)
        rgb[..., :] = FONDO
        rgb[a & b] = (200, 205, 212)
        rgb[a & ~b] = (230, 80, 70)
        rgb[~a & b] = (70, 130, 230)
        xs = 10 + i * 610
        sil.paste(Image.fromarray(rgb), (xs, 50))
        ds.text((xs, 12), f"{v.upper()}   IoU {j:.3f}", fill=(240, 246, 252), font=fuente)
    ds.text((10, 400 + 60), "gris = coinciden · rojo = sólo la referencia · azul = sólo el modelo",
            fill=(125, 133, 144), font=chica)
    hoja.save(os.path.join(SAL, "comparacion.png"))
    sil.save(os.path.join(SAL, "siluetas.png"))
    print("IoU por vista (1.00 = misma silueta):")
    for v, j in resumen:
        print(f"    {v:<10}{j:.3f}")
    print(f"    {'promedio':<10}{np.mean([j for _, j in resumen]):.3f}")
    print(f"OK  {os.path.join(SAL, 'comparacion.png')}")
    print(f"OK  {os.path.join(SAL, 'siluetas.png')}")


if __name__ == "__main__":
    main()
