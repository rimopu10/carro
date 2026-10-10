# -*- coding: utf-8 -*-
"""
Vuelca el chasis y los puntos duros a JSON para que Blender los levante.

Blender trae su propio Python (3.11) y no ve los módulos del proyecto, así que la
frontera entre los dos mundos es este archivo: aquí manda la ingeniería, allá manda
la imagen. Si cambia un tubo, se vuelve a correr esto y el render se actualiza.

Correr:  python calculos/exportar_blender.py
Salida:  cad/chasis.json
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analisis_chasis as ac                                   # noqa: E402
import carroceria as C                                         # noqa: E402

OUT = os.path.join(HERE, "..", "cad", "chasis.json")


def seccion_de(e):
    """Traduce la sección del FEM a algo que Blender pueda extruir."""
    nom = e["sec"]["nombre"]
    if nom.startswith("RED"):
        do = float(nom.split()[1].split("x")[0]) / 1000.0
        return {"tipo": "redondo", "d": round(do, 4)}
    b = float(nom.split()[1].split("x")[0]) / 1000.0
    return {"tipo": "cuadrado", "b": round(b, 4)}


tubos = []
for e in ac.elems:
    A, B = ac.NODES[e["a"]], ac.NODES[e["b"]]
    tubos.append({"a": [round(float(v), 4) for v in A],
                  "b": [round(float(v), 4) for v in B],
                  "tag": e["tag"], "nom": f"{e['a']}-{e['b']}",
                  "sec": seccion_de(e)})

# envolvente del chasis por estación: es lo que la carrocería DEBE contener
xs = np.linspace(0.0, 3.10, 64)
env_z = np.zeros_like(xs)
env_ylo = np.full_like(xs, 9.9)
env_yhi = np.zeros_like(xs)
for e in ac.elems:
    A, B = ac.NODES[e["a"]], ac.NODES[e["b"]]
    r = max(e["sec"]["c"], 0.019)
    for t in np.linspace(0, 1, 60):
        P = A + (B - A) * t
        i = int(np.clip(np.searchsorted(xs, P[0]) - 1, 0, len(xs) - 1))
        for j in (i, min(i + 1, len(xs) - 1)):
            env_z[j] = max(env_z[j], abs(P[2]) + r)
            env_ylo[j] = min(env_ylo[j], P[1] - r)
            env_yhi[j] = max(env_yhi[j], P[1] + r)
valido = env_ylo < 9
envolvente = [{"x": round(float(x), 4), "z": round(float(z), 4),
               "y_lo": round(float(a), 4), "y_hi": round(float(b), 4)}
              for x, z, a, b, ok in zip(xs, env_z, env_ylo, env_yhi, valido) if ok]

data = {
    "tubos": tubos,
    "envolvente": envolvente,
    "ruedas": [
        {"x": C.EJE_DEL, "z": +C.Z_RUEDA_DEL, "R": C.R_DEL, "W": C.ANCHO_LL, "rin": 13},
        {"x": C.EJE_DEL, "z": -C.Z_RUEDA_DEL, "R": C.R_DEL, "W": C.ANCHO_LL, "rin": 13},
        {"x": C.EJE_TRAS, "z": +C.Z_RUEDA_TRAS, "R": C.R_TRAS, "W": C.ANCHO_LL, "rin": 14},
        {"x": C.EJE_TRAS, "z": -C.Z_RUEDA_TRAS, "R": C.R_TRAS, "W": C.ANCHO_LL, "rin": 14},
    ],
    "duros": {
        "cowl": [C.X_COWL, C.Y_COWL], "cabecera": [C.X_HDR, C.Y_HDR],
        "arco": [C.X_ARCO, C.Y_ARCO], "z_espinazo": C.Z_ESPINAZO,
        "libre_real": round(float(min(e["y_lo"] for e in envolvente)), 4),
    },
    "chasis": {"tubos": len(tubos), "masa": round(float(ac.masa_acero), 1),
               "ktors": round(float(ac.K_tors))},
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, separators=(",", ":"))

print(f"OK  {len(tubos)} tubos · {len(envolvente)} estaciones de envolvente")
print(f"    semiancho maximo del chasis {max(e['z'] for e in envolvente):.3f} m")
print(f"    punto mas bajo real         {data['duros']['libre_real']:.3f} m")
print(f"    techo del chasis            {max(e['y_hi'] for e in envolvente):.3f} m")
print(f"OK  {os.path.normpath(OUT)}")
