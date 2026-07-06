# -*- coding: utf-8 -*-
"""
Incrusta el resultado del nodo generativo (JSON) dentro del visor HTML, para que
el visor no dependa de rutas del servidor (sirve solo con abrir el archivo).

Uso:  python exportar_nodo_visor.py <plantilla.html> <salida.html>
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(HERE, "..", "cad")

datos = json.load(open(os.path.join(CAD, "nodo-suspension-datos.json"), encoding="utf-8"))
plantilla = sys.argv[1]
salida = sys.argv[2]
html = open(plantilla, encoding="utf-8").read()

# Inyecta los datos como variable global antes del módulo, y neutraliza el fetch.
inject = "<script>window.__NODO__ = " + json.dumps(datos) + ";</script>\n"
html = html.replace("<script type=\"importmap\">", inject + "<script type=\"importmap\">", 1)

with open(salida, "w", encoding="utf-8") as f:
    f.write(html)
print(f"OK visor con datos incrustados: {salida}  ({len(datos['vox'])} voxels)")
