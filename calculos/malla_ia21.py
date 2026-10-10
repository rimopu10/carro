# -*- coding: utf-8 -*-
"""
Reconstrucción 3D con Hunyuan3D-2.1 — la generación siguiente a la que usamos.

Diferencia con malla_ia.py: la 2.1 es un modelo de una sola imagen (no multivista),
pero de mayor fidelidad. La apuesta aquí es distinta: en vez de darle tres vistas
chicas, se le da UNA sola grande. El detalle que sale no puede superar al que entra,
y los recortes de la lámina apenas miden 575 px de ancho.

Correr con el Python del portable:
    "C:/AI/HY3D/Hunyuan3D2_WinPortable/python_standalone/python.exe" -s -u \
        calculos/malla_ia21.py --vista lateral
"""
import os
import sys

PORT = r"C:\AI\HY3D\Hunyuan3D2_WinPortable"
os.environ.setdefault("HF_HUB_CACHE", os.path.join(PORT, "HuggingFaceHub"))
os.environ.setdefault("HY3DGEN_MODELS", os.path.join(PORT, "HuggingFaceHub"))
sys.path.insert(0, os.path.join(PORT, "Hunyuan3D-2.1"))
sys.path.insert(0, os.path.join(PORT, "Hunyuan3D-2.1", "hy3dshape"))

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(RAIZ, *os.environ.get("IA_DIR", "ref").split("/"))

from PIL import Image                                              # noqa: E402


def arg(nombre, defecto):
    return sys.argv[sys.argv.index(nombre) + 1] if nombre in sys.argv else defecto


def cargar(nombre):
    """Usa el canal ALFA del PNG si ya viene recortado.

    Volver a umbralizar aqui mordia los brillos casi blancos —las tiras de luz del
    frente— porque quedaban por encima del umbral y se marcaban como fondo."""
    import numpy as np
    f = os.path.join(REF, f"ia-{nombre}.png")
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
    from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline

    vista = arg("--vista", "lateral")
    salida = os.path.join(RAIZ, "cad", os.environ.get("IA_SALIDA", f"referencia-ia21-{vista}.glb"))
    img = cargar(vista)
    print(f"entrada: ia-{vista}.png  {img.size}")

    pipe = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
        "tencent/Hunyuan3D-2.1", subfolder="hunyuan3d-dit-v2-1",
        use_safetensors=False, device="cuda")   # el repo 2.1 publica .ckpt, no .safetensors

    pasos = int(arg("--pasos", "50"))
    octree = int(arg("--octree", "512"))
    guia = float(arg("--guia", "7.5"))
    print(f"generando ... pasos={pasos} octree={octree} guia={guia}")
    mesh = pipe(image=img, num_inference_steps=pasos, octree_resolution=octree,
                guidance_scale=guia)[0]
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    mesh.export(salida)
    print("OK malla:", salida)
    print("   vertices:", len(mesh.vertices), " caras:", len(mesh.faces))


if __name__ == "__main__":
    main()
