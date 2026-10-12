# -*- coding: utf-8 -*-
"""
Prepara la piel de Tripo para las verificaciones y el visor 3D, SIN depender de la carpeta temporal:

  cad/_vista/tripo-cerrado-sin-ruedas-mm.stl   ventanas cerradas (cerrar_invernadero) y sin las ruedas de IA.
                                               Lo usa verificar_piel_tripo.py y arreglar_chasis_tripo.py.
  cad/_vista/tripo-vista.stl                   el mismo, decimado a 150,000 caras. Lo usa visor_tripo_chasis.py.

Parte de cad/carroceria-tripo-solida-mm.stl (60 MB, NO va en git). Si falta, se regenera con:
    blender --background --python render/tripo_base.py
(necesita ref/tripo/tripo-multivista-h31.glb y Blender).

    python calculos/preparar_piel_tripo.py
Tarda ~1 minuto. Requiere: trimesh, manifold3d, fast-simplification (pip install fast-simplification).
"""
import json
import os
import sys

import manifold3d as mf
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
RAIZ = os.path.join(HERE, "..")
from maqueta import a_manifold, a_trimesh      # noqa: E402
from tripo_juguete import cerrar_invernadero   # noqa: E402

SOLIDO = os.path.join(RAIZ, "cad", "carroceria-tripo-solida-mm.stl")
SALIDA = os.path.join(RAIZ, "cad", "_vista")


def main():
    if not os.path.exists(SOLIDO):
        raise SystemExit(f"Falta {SOLIDO}. Regenerar con: blender --background --python render/tripo_base.py")
    os.makedirs(SALIDA, exist_ok=True)
    M, n = cerrar_invernadero(a_manifold(trimesh.load(SOLIDO)))
    print(f"invernadero cerrado con {n} cascos")
    ch = json.load(open(os.path.join(RAIZ, "cad", "chasis.json"), encoding="utf-8"))
    for w in ch["ruedas"]:      # cilindro alrededor de cada rueda (R + 40 mm): las ruedas de Tripo son de IA y se rehacen
        h = w["W"] * 1000 + 60
        c = mf.Manifold.cylinder(h, w["R"] * 1000 + 40, w["R"] * 1000 + 40, 48)
        M = M - c.translate([w["x"] * 1000, w["R"] * 1000, w["z"] * 1000 - h / 2])
    cerrado = a_trimesh(M)
    ruta = os.path.join(SALIDA, "tripo-cerrado-sin-ruedas-mm.stl")
    cerrado.export(ruta)
    vista = cerrado.simplify_quadric_decimation(face_count=150000)
    vista.export(os.path.join(SALIDA, "tripo-vista.stl"))
    print("OK", SALIDA, f"({len(cerrado.faces)} -> {len(vista.faces)} caras)")


if __name__ == "__main__":
    main()
