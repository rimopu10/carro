# -*- coding: utf-8 -*-
"""
Perfiles de impresora: lo que se adapta a UNA impresora vive aquí, no en el diseño.

Sin perfil, los generadores (tripo_juguete, tripo_gaviota) usan sus medidas de diseño y
escriben en impresion/. Con `--impresora NOMBRE` leen impresion/impresoras/NOMBRE.json,
ajustan holguras y agujeros a esa máquina y escriben en impresion/NOMBRE/. Cambiar de
impresora = otro JSON; el diseño y las salidas de otras impresoras no se tocan.
"""
import json
import os

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NEUTRO = {"nombre": "neutro (medidas de diseño)", "cama_mm": [220, 220, 250], "brim_mm": 0,
          "margen_mm": 4, "compensa_agujero_mm": 0.0, "holgura_puerta_mm": None}


def cargar(nombre=None):
    if not nombre:
        p = dict(NEUTRO)
        p["clave"] = None
        p["salida"] = os.path.normpath(os.path.join(RAIZ, "impresion"))
        return p
    ruta = os.path.join(RAIZ, "impresion", "impresoras", f"{nombre}.json")
    p = dict(NEUTRO)
    p.update(json.load(open(ruta, encoding="utf-8")))
    p["clave"] = nombre
    p["salida"] = os.path.normpath(os.path.join(RAIZ, "impresion", nombre))
    os.makedirs(p["salida"], exist_ok=True)
    return p


def util_mm(p):
    """Lo más grande que cabe en la cama contando el brim y un margen por lado."""
    return p["cama_mm"][0] - 2 * p["brim_mm"] - 2 * p["margen_mm"]
