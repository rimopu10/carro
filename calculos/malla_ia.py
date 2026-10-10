# -*- coding: utf-8 -*-
"""
Reconstruye la carrocería de la referencia en 3D con Hunyuan3D-2 (imagen -> malla).

Por qué: el casco visual sólo da la envolvente y no puede meter concavidades — la
toma de aire hundida, el undercut del costado, el rebaje del difusor. Un modelo de
imagen-a-3D sí las reconstruye. Aquí se usa en MODO MULTIVISTA con las cuatro vistas
de puertas cerradas de la lámina, que da mucho más fidelidad que una sola imagen.

Sólo se genera GEOMETRÍA (no textura): la textura pide más VRAM y no sirve de nada
porque la pintura y los materiales se ponen después en Blender.

Licencia: los pesos de Hunyuan3D son NO COMERCIALES. Para un carro propio está bien;
si esto alguna vez se vendiera, hay que rehacer la superficie sin ellos.

Se corre con el Python del paquete portable, no con el del sistema:
    "C:/AI/HY3D/Hunyuan3D2_WinPortable/python_standalone/python.exe" -s calculos/malla_ia.py
"""
import os
import sys

PORT = r"C:\AI\HY3D\Hunyuan3D2_WinPortable"
os.environ.setdefault("HF_HUB_CACHE", os.path.join(PORT, "HuggingFaceHub"))
os.environ.setdefault("HY3DGEN_MODELS", os.path.join(PORT, "HuggingFaceHub"))
sys.path.insert(0, os.path.join(PORT, "Hunyuan3D-2"))

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(RAIZ, "ref")
DIR = os.path.join(RAIZ, *os.environ.get("IA_DIR", "ref").split("/"))
SALIDA = os.path.join(RAIZ, "cad", os.environ.get("IA_SALIDA", "referencia-ia.glb"))

from PIL import Image                                              # noqa: E402


def cargar(nombre):
    """Usa el canal ALFA del PNG si ya viene recortado.

    Volver a umbralizar aqui mordia los brillos casi blancos —las tiras de luz del
    frente— porque quedaban por encima del umbral y se marcaban como fondo."""
    import numpy as np
    f = os.path.join(DIR, f"ia-{nombre}.png")
    if not os.path.exists(f):
        return None
    im = Image.open(f)
    if im.mode == "RGBA" and np.asarray(im)[:, :, 3].min() < 250:
        return im
    from scipy import ndimage
    a = np.asarray(im.convert("RGB"))
    alpha = ndimage.binary_fill_holes(a.min(axis=2) < 244)
    return Image.fromarray(np.dstack([a, (alpha * 255).astype("uint8")]), "RGBA")
def main():
    from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

    # SIN la vista trasera a proposito: siendo una ortografica plana, el modelo la
    # interpreta como un panel y lo deja parado contra la cola, tapando el afilado
    # real. Se le dan los dos costados en su lugar (el carro es simetrico).
    pedidas = os.environ.get("IA_VISTAS", "front:frontal,left:lateral,right:lateral-espejo")
    vistas = {}
    for par in pedidas.split(","):
        k, v = par.split(":")
        vistas[k] = cargar(v)
    vistas = {k: v for k, v in vistas.items() if v is not None}
    print("vistas disponibles:", list(vistas))

    # NO turbo: el turbo destila el muestreo a pocos pasos y redondea todo. Para
    # geometria con aristas (splitter, tomas, labios de salpicadera) hay que usar el
    # modelo completo con mas pasos, aunque tarde.
    modelo = os.environ.get("HY3D_MODELO", "tencent/Hunyuan3D-2mv")
    sub = os.environ.get("HY3D_SUB", "hunyuan3d-dit-v2-mv")
    print(f"cargando {modelo} / {sub} ...")
    pipe = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
        modelo, subfolder=sub, use_safetensors=True, device="cuda")
    # dmc daria aristas mas limpias pero necesita el paquete diso, que no compila aqui
    # (falla el wheel build). Se queda mc; el salto de calidad viene de octree 512,
    pipe.enable_flashvdm(mc_algo=os.environ.get("HY3D_MC", "mc"))

    pasos = int(os.environ.get("HY3D_PASOS", "50"))
    octree = int(os.environ.get("HY3D_OCTREE", "512"))
    guia = float(os.environ.get("HY3D_GUIA", "7.0"))
    print(f"generando geometria ... pasos={pasos} octree={octree} guia={guia}")
    mesh = pipe(image=vistas, num_inference_steps=pasos, octree_resolution=octree,
                guidance_scale=guia, generator=None)[0]
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    mesh.export(SALIDA)
    print("OK malla:", SALIDA)
    print("   vertices:", len(mesh.vertices), " caras:", len(mesh.faces))


if __name__ == "__main__":
    main()
